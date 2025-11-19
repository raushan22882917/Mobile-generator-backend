"""
Fast Generate Endpoint
Optimized endpoint that returns immediately and processes in background
"""
import asyncio
import logging
import uuid
from fastapi import APIRouter, Depends
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
        logger.info(f"Starting background generation for project {project_id}")
        
        generator = await create_streaming_generator()
        
        async def send_progress(update: ProgressUpdate):
            """Send progress via WebSocket"""
            try:
                await connection_manager.send_to_project(
                    project_id,
                    {
                        "type": "progress",
                        "data": update.to_dict()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send progress update via WebSocket: {e}")
        
        # Generate with fast mode (skip extra screens for speed)
        result = await generator.generate_with_streaming(
            prompt=prompt,
            user_id=user_id,
            project_id=project_id,
            progress_callback=send_progress,
            skip_screens=True  # Fast mode
        )
        
        # Send completion
        try:
            await connection_manager.send_to_project(
                project_id,
                {
                    "type": "complete",
                    "data": result
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send completion via WebSocket: {e}")
        
        logger.info(f"Background generation complete for {project_id}")
        
    except Exception as e:
        logger.error(f"Background generation failed for {project_id}: {e}", exc_info=True)
        
        # Update project status to error
        try:
            from main import project_manager
            import models.project
            project_manager.update_project_status(
                project_id,
                models.project.ProjectStatus.ERROR,
                error_message=str(e)
            )
        except Exception as status_error:
            logger.error(f"Failed to update project status to error: {status_error}")
        
        # Try to send error via WebSocket
        try:
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
        except Exception as ws_error:
            logger.warning(f"Failed to send error via WebSocket: {ws_error}")


@router.post("/fast-generate", response_model=FastGenerateResponse)
async def fast_generate(
    request: FastGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Fast generation endpoint - returns immediately
    
    This endpoint:
    1. Validates input
    2. Creates project placeholder
    3. Returns project_id immediately
    4. Processes generation in background
    5. Sends updates via WebSocket
    
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
    
    # Create project placeholder immediately so status can be tracked
    from main import project_manager
    import models.project
    from datetime import datetime
    from pathlib import Path
    
    # Create project with specific ID
    project = models.project.Project(
        id=project_id,
        user_id=sanitized_user_id,
        prompt=sanitized_prompt,
        directory=str(Path(project_manager.base_dir) / project_id),
        port=project_manager.port_manager.allocate_port(),
        status=models.project.ProjectStatus.INITIALIZING,
        created_at=datetime.now(),
        last_active=datetime.now()
    )
    
    # Initialize build steps (same as in project_manager.create_project)
    from models.project import BuildStep, BuildStepStatus
    project.build_steps = [
        BuildStep(
            id="step_1",
            name="Create App",
            description="Initializing project structure",
            status=BuildStepStatus.PENDING,
            progress=0
        ),
        BuildStep(
            id="step_2",
            name="Add Login & Signup",
            description="Creating authentication screens",
            status=BuildStepStatus.PENDING,
            progress=0
        ),
        BuildStep(
            id="step_3",
            name="Update index.tsx",
            description="Setting up navigation and routing",
            status=BuildStepStatus.PENDING,
            progress=0
        ),
        BuildStep(
            id="step_4",
            name="Add App Screens",
            description="Generating app screens with dummy data",
            status=BuildStepStatus.PENDING,
            progress=0
        ),
        BuildStep(
            id="step_5",
            name="Setup Preview",
            description="Installing dependencies and starting server",
            status=BuildStepStatus.PENDING,
            progress=0
        ),
    ]
    
    # Add to active projects
    project_manager.active_projects[project_id] = project
    
    logger.info(f"Project {project_id} created and ready for background generation")
    
    # Start background generation using asyncio.create_task for better reliability
    # BackgroundTasks may not be suitable for long-running tasks
    import asyncio
    asyncio.create_task(
        generate_in_background(
            project_id,
            sanitized_prompt,
            sanitized_user_id,
            request.template_id
        )
    )
    
    # Return immediately
    return FastGenerateResponse(
        project_id=project_id,
        status="processing",
        message="Generation started. Connect to WebSocket for updates.",
        websocket_url=f"/api/v1/ws/generate/{project_id}"
    )
