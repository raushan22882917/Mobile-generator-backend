"""
Fast Generate Endpoint
Optimized endpoint that returns immediately and processes in background
"""
import asyncio
import logging
import uuid
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from services.streaming_generator import StreamingGenerator, ProgressUpdate
from services.websocket_manager import connection_manager
from middleware.auth import verify_api_key
from utils.sanitization import sanitize_prompt, sanitize_user_id, SanitizationError
from exceptions import ValidationError, ResourceLimitError

logger = logging.getLogger(__name__)

router = APIRouter()


class FastGenerateRequest(BaseModel):
    """Request model for fast generation"""
    prompt: str = Field(..., min_length=10, max_length=5000)
    user_id: Optional[str] = Field(default="anonymous")
    template_id: Optional[str] = Field(default=None)


class FastGenerateResponse(BaseModel):
    """Response model for fast generation"""
    project_id: str
    status: str
    message: str
    websocket_url: str


async def create_streaming_generator():
    """Get streaming generator instance"""
    from main import (
        code_generator,
        screen_generator,
        project_manager,
        command_executor,
        tunnel_manager,
        cloud_storage_manager,
        resource_monitor
    )
    
    # Check capacity
    can_accept, reason = resource_monitor.can_accept_new_project(
        project_manager.get_active_project_count()
    )
    
    if not can_accept:
        raise ResourceLimitError(reason)
    
    return StreamingGenerator(
        code_generator=code_generator,
        screen_generator=screen_generator,
        project_manager=project_manager,
        command_executor=command_executor,
        tunnel_manager=tunnel_manager,
        cloud_storage_manager=cloud_storage_manager
    )


async def generate_in_background(
    project_id: str,
    prompt: str,
    user_id: str,
    template_id: Optional[str] = None
):
    """Generate app in background and send updates via WebSocket"""
    try:
        generator = await create_streaming_generator()
        
        async def send_progress(update: ProgressUpdate):
            """Send progress via WebSocket"""
            await connection_manager.send_to_project(
                project_id,
                {
                    "type": "progress",
                    "data": update.to_dict()
                }
            )
        
        # Generate with fast mode (skip extra screens for speed)
        result = await generator.generate_with_streaming(
            prompt=prompt,
            user_id=user_id,
            project_id=project_id,
            progress_callback=send_progress,
            skip_screens=True  # Fast mode
        )
        
        # Send completion
        await connection_manager.send_to_project(
            project_id,
            {
                "type": "complete",
                "data": result
            }
        )
        
        logger.info(f"Background generation complete for {project_id}")
        
    except Exception as e:
        logger.error(f"Background generation failed: {e}", exc_info=True)
        await connection_manager.send_to_project(
            project_id,
            {
                "type": "error",
                "data": {
                    "error": str(e),
                    "message": str(e)
                }
            }
        )


@router.post("/fast-generate", response_model=FastGenerateResponse)
async def fast_generate(
    request: FastGenerateRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Fast generation endpoint - returns immediately
    
    This endpoint:
    1. Validates input
    2. Returns project_id immediately
    3. Processes generation in background
    4. Sends updates via WebSocket
    
    Client should connect to WebSocket to receive updates.
    """
    try:
        # Sanitize inputs
        sanitized_prompt = sanitize_prompt(request.prompt)
        sanitized_user_id = sanitize_user_id(request.user_id)
    except SanitizationError as e:
        logger.warning(f"Input sanitization failed: {str(e)}")
        raise ValidationError(str(e))
    
    # Generate project ID
    project_id = str(uuid.uuid4())
    
    logger.info(f"Fast generate initiated for project {project_id}")
    
    # Start background generation
    background_tasks.add_task(
        generate_in_background,
        project_id,
        sanitized_prompt,
        sanitized_user_id,
        request.template_id
    )
    
    # Return immediately
    return FastGenerateResponse(
        project_id=project_id,
        status="processing",
        message="Generation started. Connect to WebSocket for updates.",
        websocket_url=f"/api/v1/ws/generate/{project_id}"
    )
