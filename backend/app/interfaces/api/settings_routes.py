from fastapi import APIRouter, Depends
import logging
from app.interfaces.dependencies import get_current_user
from app.interfaces.schemas.base import APIResponse
from app.core.config import get_settings
from app.domain.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

PREDEFINED_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "deepseek-chat",
    "deepseek-reasoner",
    "openai",
    "mistral-large-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]


@router.get("")
async def get_settings_info(
    current_user: User = Depends(get_current_user)
):
    """Get current application settings"""
    settings = get_settings()
    
    available = list(PREDEFINED_MODELS)
    if settings.model_name and settings.model_name not in available:
        available.insert(0, settings.model_name)
    
    return APIResponse.success({
        "model_name": settings.model_name,
        "api_base": settings.api_base,
        "available_models": available,
        "auth_provider": settings.auth_provider,
        "search_provider": settings.search_provider,
    })
