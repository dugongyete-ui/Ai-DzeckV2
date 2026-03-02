import logging
from typing import Optional

import inngest

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_inngest_client: Optional[inngest.Inngest] = None
_inngest_functions = []


def get_inngest_client() -> Optional[inngest.Inngest]:
    """Get the Inngest client singleton. Returns None if not configured."""
    global _inngest_client
    if _inngest_client is not None:
        return _inngest_client

    settings = get_settings()
    if not settings.inngest_api_key or not settings.inngest_signing_key:
        logger.warning(
            "Inngest is not fully configured (missing INNGEST_API_KEY or "
            "INNGEST_SIGNING_KEY). Inngest features are disabled."
        )
        return None

    _inngest_client = inngest.Inngest(
        app_id=settings.inngest_app_id,
        event_key=settings.inngest_api_key,
        signing_key=settings.inngest_signing_key,
        is_production=True,
        logger=logger,
    )
    logger.info(f"Inngest client initialized for app: {settings.inngest_app_id}")
    return _inngest_client


def get_inngest_functions() -> list:
    """Return all registered Inngest functions."""
    return _inngest_functions


def _build_functions(client: inngest.Inngest) -> list:
    """Define and return all Inngest functions for the app."""

    @client.create_function(
        fn_id="agent-task-started",
        trigger=inngest.TriggerEvent(event="dzeck/agent.task.started"),
    )
    async def on_agent_task_started(ctx: inngest.Context, step: inngest.Step) -> dict:
        """Triggered when an agent task starts. Logs and can add retries/hooks."""
        data = ctx.event.data or {}
        session_id = data.get("session_id", "unknown")
        agent_id = data.get("agent_id", "unknown")
        logger.info(
            f"[Inngest] Agent task started — session={session_id}, agent={agent_id}"
        )
        return {"status": "acknowledged", "session_id": session_id}

    @client.create_function(
        fn_id="agent-task-completed",
        trigger=inngest.TriggerEvent(event="dzeck/agent.task.completed"),
    )
    async def on_agent_task_completed(
        ctx: inngest.Context, step: inngest.Step
    ) -> dict:
        """Triggered when an agent task completes successfully."""
        data = ctx.event.data or {}
        session_id = data.get("session_id", "unknown")
        logger.info(f"[Inngest] Agent task completed — session={session_id}")
        return {"status": "acknowledged", "session_id": session_id}

    @client.create_function(
        fn_id="agent-task-failed",
        trigger=inngest.TriggerEvent(event="dzeck/agent.task.failed"),
        retries=3,
    )
    async def on_agent_task_failed(ctx: inngest.Context, step: inngest.Step) -> dict:
        """Triggered when an agent task fails. Retries up to 3 times."""
        data = ctx.event.data or {}
        session_id = data.get("session_id", "unknown")
        error = data.get("error", "unknown error")
        logger.error(
            f"[Inngest] Agent task failed — session={session_id}, error={error}"
        )
        return {"status": "acknowledged", "session_id": session_id, "error": error}

    return [on_agent_task_started, on_agent_task_completed, on_agent_task_failed]


def setup_inngest(app) -> bool:
    """
    Register Inngest endpoint on the FastAPI app.
    Returns True if Inngest was configured, False otherwise.
    """
    from inngest.fast_api import serve

    client = get_inngest_client()
    if client is None:
        logger.warning("Inngest not configured — skipping endpoint registration.")
        return False

    global _inngest_functions
    _inngest_functions = _build_functions(client)

    serve(app, client, _inngest_functions, serve_path="/api/inngest")
    logger.info("Inngest endpoint registered at /api/inngest")
    return True


async def send_inngest_event(event_name: str, data: dict) -> bool:
    """
    Send an event to Inngest. Safe to call even if Inngest is not configured.
    Returns True if the event was sent, False otherwise.
    """
    client = get_inngest_client()
    if client is None:
        return False
    try:
        await client.send(inngest.Event(name=event_name, data=data))
        logger.debug(f"[Inngest] Event sent: {event_name}")
        return True
    except Exception as e:
        logger.error(f"[Inngest] Failed to send event {event_name}: {e}")
        return False
