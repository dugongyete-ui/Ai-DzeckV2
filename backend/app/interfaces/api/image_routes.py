import httpx
import logging
from urllib.parse import quote
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from app.interfaces.dependencies import get_current_user
from app.domain.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])

POLLINATIONS_IMAGE_BASE = "https://image.pollinations.ai/prompt"


@router.get("/generate")
async def generate_image(
    prompt: str = Query(..., description="Image prompt text"),
    width: int = Query(1024, description="Image width"),
    height: int = Query(1024, description="Image height"),
    seed: int = Query(42, description="Random seed"),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an image using Pollinations AI image API.
    Returns the image URL or proxies the image directly.
    """
    encoded_prompt = quote(prompt)
    image_url = f"{POLLINATIONS_IMAGE_BASE}/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
    
    logger.info(f"Generating image for prompt: {prompt[:50]}...")
    
    return JSONResponse(content={
        "url": image_url,
        "prompt": prompt,
        "width": width,
        "height": height,
    })


@router.get("/proxy")
async def proxy_image(
    prompt: str = Query(..., description="Image prompt text"),
    width: int = Query(1024, description="Image width"),
    height: int = Query(1024, description="Image height"),
    seed: int = Query(42, description="Random seed"),
    current_user: User = Depends(get_current_user)
):
    """
    Proxy image from Pollinations AI — streams the image bytes back to the client.
    Use this endpoint when you want to embed the image directly.
    """
    encoded_prompt = quote(prompt)
    image_url = f"{POLLINATIONS_IMAGE_BASE}/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
    
    logger.info(f"Proxying image for prompt: {prompt[:50]}...")
    
    async def image_stream():
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream("GET", image_url) as response:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk
    
    return StreamingResponse(
        image_stream(),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}
    )
