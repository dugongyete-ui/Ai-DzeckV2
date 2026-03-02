"""
HybridSandbox: E2B untuk eksekusi kode/terminal, Docker lokal untuk browser/VNC.

Arsitektur:
  - exec_command (shell/terminal)  → E2B cloud (isolated, secure)
  - view_shell / shell session     → E2B cloud
  - file_write                     → local + E2B (sync agar kode bisa akses file)
  - file_read / list / find etc    → local (source of truth)
  - file_upload                    → local + E2B (sync)
  - get_browser / VNC / CDP        → local Docker sandbox
  - destroy                        → keduanya

Dengan ini E2B aktif dipakai untuk semua eksekusi kode/terminal,
sementara browser/VNC tetap berjalan di local sandbox.
"""

import io
import logging
from typing import BinaryIO, Optional

from app.core.config import get_settings
from app.domain.external.browser import Browser
from app.domain.external.sandbox import Sandbox
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

_SEPARATOR = "|e2b:"
_DOCKER_PREFIX = "docker:"


def _encode_id(docker_id: str, e2b_id: str) -> str:
    """Encode both sandbox IDs into a single composite string."""
    return f"{_DOCKER_PREFIX}{docker_id}{_SEPARATOR}{e2b_id}"


def _decode_id(composite_id: str):
    """Decode composite ID back into (docker_id, e2b_id). Returns (None, None) on failure."""
    try:
        if _SEPARATOR in composite_id:
            parts = composite_id.split(_SEPARATOR, 1)
            docker_id = parts[0].replace(_DOCKER_PREFIX, "")
            e2b_id = parts[1]
            return docker_id, e2b_id
    except Exception:
        pass
    return None, None


class HybridSandbox(Sandbox):
    """
    Sandbox hibrida: E2B untuk eksekusi kode, Docker lokal untuk browser/VNC.

    Digunakan secara otomatis ketika E2B_API_KEY tersedia.
    """

    def __init__(self, local_sandbox, e2b_sandbox):
        self._local = local_sandbox
        self._e2b = e2b_sandbox

    @property
    def id(self) -> str:
        return _encode_id(self._local.id, self._e2b.id)

    @property
    def vnc_url(self) -> Optional[str]:
        return getattr(self._local, "vnc_url", None)

    @property
    def cdp_url(self) -> Optional[str]:
        return getattr(self._local, "cdp_url", None)

    async def ensure_sandbox(self) -> None:
        await self._local.ensure_sandbox()
        await self._e2b.ensure_sandbox()

    async def exec_command(
        self, session_id: str, exec_dir: str, command: str
    ) -> ToolResult:
        """Eksekusi shell command di E2B cloud (terisolasi dan aman)."""
        logger.debug(f"[HybridSandbox] exec via E2B: {command[:60]}")
        return await self._e2b.exec_command(session_id, exec_dir, command)

    async def view_shell(self, session_id: str, console: bool = False) -> ToolResult:
        return await self._e2b.view_shell(session_id, console)

    async def wait_for_process(
        self, session_id: str, seconds: Optional[int] = None
    ) -> ToolResult:
        return await self._e2b.wait_for_process(session_id, seconds)

    async def write_to_process(
        self, session_id: str, input_text: str, press_enter: bool = True
    ) -> ToolResult:
        return await self._e2b.write_to_process(session_id, input_text, press_enter)

    async def kill_process(self, session_id: str) -> ToolResult:
        return await self._e2b.kill_process(session_id)

    async def file_write(
        self,
        file: str,
        content: str,
        append: bool = False,
        leading_newline: bool = False,
        trailing_newline: bool = False,
        sudo: bool = False,
    ) -> ToolResult:
        """
        Tulis file ke local sandbox (sumber kebenaran).
        Juga sync ke E2B supaya kode yang berjalan di E2B bisa mengakses file.
        """
        result = await self._local.file_write(
            file, content, append, leading_newline, trailing_newline, sudo
        )
        if result.success:
            try:
                await self._e2b.file_write(
                    file, content, append, leading_newline, trailing_newline, sudo
                )
            except Exception as e:
                logger.warning(f"[HybridSandbox] E2B file sync failed for {file}: {e}")
        return result

    async def file_read(
        self,
        file: str,
        start_line: int = None,
        end_line: int = None,
        sudo: bool = False,
    ) -> ToolResult:
        return await self._local.file_read(file, start_line, end_line, sudo)

    async def file_exists(self, path: str) -> ToolResult:
        return await self._local.file_exists(path)

    async def file_delete(self, path: str) -> ToolResult:
        result = await self._local.file_delete(path)
        if result.success:
            try:
                await self._e2b.file_delete(path)
            except Exception as e:
                logger.warning(f"[HybridSandbox] E2B file delete sync failed: {e}")
        return result

    async def file_list(self, path: str) -> ToolResult:
        return await self._local.file_list(path)

    async def file_replace(
        self, file: str, old_str: str, new_str: str, sudo: bool = False
    ) -> ToolResult:
        result = await self._local.file_replace(file, old_str, new_str, sudo)
        if result.success:
            try:
                await self._e2b.file_replace(file, old_str, new_str, sudo)
            except Exception as e:
                logger.warning(f"[HybridSandbox] E2B file_replace sync failed: {e}")
        return result

    async def file_search(
        self, file: str, regex: str, sudo: bool = False
    ) -> ToolResult:
        return await self._local.file_search(file, regex, sudo)

    async def file_find(self, path: str, glob_pattern: str) -> ToolResult:
        return await self._local.file_find(path, glob_pattern)

    async def file_upload(
        self, file_data: BinaryIO, path: str, filename: str = None
    ) -> ToolResult:
        """Upload ke local, sync copy ke E2B supaya kode bisa akses."""
        data = file_data.read()
        result = await self._local.file_upload(io.BytesIO(data), path, filename)
        if result.success:
            try:
                await self._e2b.file_upload(io.BytesIO(data), path, filename)
            except Exception as e:
                logger.warning(f"[HybridSandbox] E2B file upload sync failed: {e}")
        return result

    async def file_download(self, path: str) -> BinaryIO:
        return await self._local.file_download(path)

    async def get_browser(self) -> Browser:
        """Browser/VNC tetap menggunakan local Docker sandbox."""
        return await self._local.get_browser()

    async def destroy(self) -> bool:
        local_ok = await self._local.destroy()
        e2b_ok = await self._e2b.destroy()
        return local_ok and e2b_ok

    @classmethod
    async def create(cls) -> "HybridSandbox":
        from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
        from app.infrastructure.external.sandbox.e2b_sandbox import E2BSandbox

        settings = get_settings()
        logger.info("[HybridSandbox] Creating hybrid sandbox (Docker + E2B)...")

        local = await DockerSandbox.create()
        logger.info(f"[HybridSandbox] Docker sandbox ready: {local.id}")

        try:
            e2b = await E2BSandbox.create()
            logger.info(f"[HybridSandbox] E2B sandbox ready: {e2b.id}")
        except Exception as e:
            logger.error(
                f"[HybridSandbox] E2B sandbox creation failed: {e}. "
                "Falling back to Docker-only mode."
            )
            return local

        return cls(local_sandbox=local, e2b_sandbox=e2b)

    @classmethod
    async def get(cls, sandbox_id: str) -> "HybridSandbox":
        from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
        from app.infrastructure.external.sandbox.e2b_sandbox import E2BSandbox

        docker_id, e2b_id = _decode_id(sandbox_id)

        if not docker_id or not e2b_id:
            logger.warning(
                f"[HybridSandbox] Cannot decode hybrid ID '{sandbox_id}', "
                "falling back to DockerSandbox.get()"
            )
            return await DockerSandbox.get(sandbox_id)

        local = await DockerSandbox.get(docker_id)
        try:
            e2b = await E2BSandbox.get(e2b_id)
        except Exception as e:
            logger.warning(
                f"[HybridSandbox] E2B reconnect failed: {e}. Creating new E2B sandbox."
            )
            e2b = await E2BSandbox.create()

        return cls(local_sandbox=local, e2b_sandbox=e2b)
