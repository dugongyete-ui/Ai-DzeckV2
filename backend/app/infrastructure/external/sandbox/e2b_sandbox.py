import io
import logging
from typing import BinaryIO, Dict, Optional

from app.core.config import get_settings
from app.domain.external.browser import Browser
from app.domain.external.sandbox import Sandbox
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class E2BSandbox(Sandbox):
    """E2B cloud sandbox implementation of the Sandbox protocol."""

    def __init__(self, sandbox_id: str, sandbox_obj):
        self._sandbox_id = sandbox_id
        self._sandbox = sandbox_obj
        self._shell_outputs: Dict[str, str] = {}

    @property
    def id(self) -> str:
        return self._sandbox_id

    @property
    def vnc_url(self) -> Optional[str]:
        return None

    @property
    def cdp_url(self) -> Optional[str]:
        return None

    async def ensure_sandbox(self) -> None:
        is_running = await self._sandbox.is_running()
        if not is_running:
            raise Exception("E2B sandbox is not running")
        logger.info(f"E2B sandbox {self._sandbox_id} is ready")

    async def exec_command(
        self, session_id: str, exec_dir: str, command: str
    ) -> ToolResult:
        try:
            full_command = f"cd {exec_dir} && {command}"
            result = await self._sandbox.commands.run(full_command, timeout=120)
            output = result.stdout or ""
            if result.stderr:
                output += f"\n{result.stderr}" if output else result.stderr
            self._shell_outputs[session_id] = output
            return ToolResult(
                success=result.exit_code == 0,
                message=output or "Command completed",
                data={"output": output, "exit_code": result.exit_code},
            )
        except Exception as e:
            logger.error(f"E2B exec_command error: {e}")
            return ToolResult(success=False, message=str(e))

    async def view_shell(self, session_id: str, console: bool = False) -> ToolResult:
        output = self._shell_outputs.get(session_id, "")
        return ToolResult(
            success=True,
            message=output or "No output",
            data={"output": output},
        )

    async def wait_for_process(
        self, session_id: str, seconds: Optional[int] = None
    ) -> ToolResult:
        return ToolResult(success=True, message="Process completed")

    async def write_to_process(
        self, session_id: str, input_text: str, press_enter: bool = True
    ) -> ToolResult:
        return ToolResult(
            success=False,
            message="Interactive process input not supported in E2B sandbox",
        )

    async def kill_process(self, session_id: str) -> ToolResult:
        return ToolResult(success=True, message="Process killed")

    async def file_write(
        self,
        file: str,
        content: str,
        append: bool = False,
        leading_newline: bool = False,
        trailing_newline: bool = False,
        sudo: bool = False,
    ) -> ToolResult:
        try:
            if append:
                existing = ""
                try:
                    raw = await self._sandbox.files.read(file)
                    existing = raw if isinstance(raw, str) else raw.decode("utf-8")
                except Exception:
                    pass
                content = existing + content
            if leading_newline:
                content = "\n" + content
            if trailing_newline:
                content = content + "\n"
            await self._sandbox.files.write(file, content)
            return ToolResult(success=True, message=f"File written: {file}")
        except Exception as e:
            logger.error(f"E2B file_write error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_read(
        self,
        file: str,
        start_line: int = None,
        end_line: int = None,
        sudo: bool = False,
    ) -> ToolResult:
        try:
            raw = await self._sandbox.files.read(file)
            content = raw if isinstance(raw, str) else raw.decode("utf-8")
            if start_line is not None or end_line is not None:
                lines = content.splitlines()
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else len(lines)
                content = "\n".join(lines[start:end])
            return ToolResult(success=True, message=content, data={"content": content})
        except Exception as e:
            logger.error(f"E2B file_read error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_exists(self, path: str) -> ToolResult:
        try:
            exists = await self._sandbox.files.exists(path)
            return ToolResult(success=True, message=str(exists), data={"exists": exists})
        except Exception as e:
            return ToolResult(success=False, message=str(e))

    async def file_delete(self, path: str) -> ToolResult:
        try:
            await self._sandbox.files.remove(path)
            return ToolResult(success=True, message=f"Deleted: {path}")
        except Exception as e:
            logger.error(f"E2B file_delete error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_list(self, path: str) -> ToolResult:
        try:
            entries = await self._sandbox.files.list(path)
            items = [
                {"name": e.name, "type": "dir" if e.is_dir else "file"}
                for e in entries
            ]
            return ToolResult(success=True, message="OK", data={"files": items})
        except Exception as e:
            logger.error(f"E2B file_list error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_replace(
        self, file: str, old_str: str, new_str: str, sudo: bool = False
    ) -> ToolResult:
        try:
            result = await self.file_read(file)
            if not result.success:
                return result
            content = result.data["content"]
            if old_str not in content:
                return ToolResult(success=False, message="String not found in file")
            new_content = content.replace(old_str, new_str, 1)
            return await self.file_write(file, new_content)
        except Exception as e:
            logger.error(f"E2B file_replace error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_search(
        self, file: str, regex: str, sudo: bool = False
    ) -> ToolResult:
        try:
            cmd_result = await self._sandbox.commands.run(
                f"grep -n '{regex}' '{file}' 2>&1 || true"
            )
            output = cmd_result.stdout or ""
            return ToolResult(success=True, message=output, data={"matches": output})
        except Exception as e:
            logger.error(f"E2B file_search error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_find(self, path: str, glob_pattern: str) -> ToolResult:
        try:
            cmd_result = await self._sandbox.commands.run(
                f"find '{path}' -name '{glob_pattern}' 2>&1 || true"
            )
            output = cmd_result.stdout or ""
            files = [f for f in output.splitlines() if f.strip()]
            return ToolResult(success=True, message="OK", data={"files": files})
        except Exception as e:
            logger.error(f"E2B file_find error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_upload(
        self, file_data: BinaryIO, path: str, filename: str = None
    ) -> ToolResult:
        try:
            data = file_data.read()
            await self._sandbox.files.write(path, data)
            return ToolResult(success=True, message=f"File uploaded to {path}")
        except Exception as e:
            logger.error(f"E2B file_upload error: {e}")
            return ToolResult(success=False, message=str(e))

    async def file_download(self, path: str) -> BinaryIO:
        raw = await self._sandbox.files.read(path)
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        return io.BytesIO(raw)

    async def get_browser(self) -> Browser:
        raise NotImplementedError(
            "Browser/VNC is not supported in E2B sandbox. "
            "Switch to SANDBOX_PROVIDER=docker for browser features."
        )

    async def destroy(self) -> bool:
        try:
            await self._sandbox.kill()
            logger.info(f"E2B sandbox {self._sandbox_id} destroyed")
            return True
        except Exception as e:
            logger.error(f"E2B destroy error: {e}")
            return False

    @classmethod
    async def create(cls) -> "E2BSandbox":
        from e2b import AsyncSandbox

        settings = get_settings()
        if not settings.e2b_api_key:
            raise ValueError(
                "E2B_API_KEY is not configured. "
                "Set it in your environment secrets."
            )
        logger.info("Creating E2B cloud sandbox...")
        sandbox = await AsyncSandbox.create(
            api_key=settings.e2b_api_key,
            timeout=settings.sandbox_ttl_minutes * 60 if settings.sandbox_ttl_minutes else 1800,
        )
        logger.info(f"E2B sandbox created: {sandbox.sandbox_id}")
        return cls(sandbox_id=sandbox.sandbox_id, sandbox_obj=sandbox)

    @classmethod
    async def get(cls, sandbox_id: str) -> "E2BSandbox":
        from e2b import AsyncSandbox

        settings = get_settings()
        if not settings.e2b_api_key:
            raise ValueError("E2B_API_KEY is not configured.")
        sandbox = await AsyncSandbox.connect(sandbox_id, api_key=settings.e2b_api_key)
        return cls(sandbox_id=sandbox_id, sandbox_obj=sandbox)
