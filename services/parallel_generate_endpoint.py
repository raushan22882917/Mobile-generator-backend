"""
Parallel Generate Endpoint
New endpoint that uses parallel workflow for screen generation
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging
import time
import random
import string
import os

from middleware.auth import verify_api_key
from utils.sanitization import sanitize_prompt, sanitize_user_id, SanitizationError
from exceptions import ResourceLimitError, ValidationError
import models.project

logger = logging.getLogger(__name__)

router = APIRouter()


class ParallelGenerateRequest(BaseModel):
    """Request model for /generate-parallel endpoint"""
    prompt: str = Field(..., min_length=10, max_length=5000, description="Natural language description of the app")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")
    template_id: Optional[str] = Field(default=None, description="UI template ID to apply")


class ParallelGenerateResponse(BaseModel):
    """Response model for /generate-parallel endpoint"""
    project_id: str
    preview_url: Optional[str] = None
    status: str
    message: str
    screens_created: list[str]
    created_at: str


@router.post("/generate-parallel", response_model=ParallelGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_parallel(
    request: ParallelGenerateRequest,
    api_key: str = Depends(verify_api_key),
    # Inject dependencies
    code_generator=None,
    project_manager=None,
    command_executor=None,
    resource_monitor=None,
    parallel_workflow=None
):
    """
    Generate a new Expo application with parallel workflow:
    1. Check system capacity
    2. Create Expo project
    3. In parallel:
       - Generate screens using AI (including auth.tsx)
       - Create ngrok tunnel for mobile preview
    4. Install dependencies
    5. Start Expo server
    
    Returns project ID, preview URL, and list of created screens.
    """
    start_time = time.time()
    
    # Sanitize inputs
    try:
        sanitized_prompt = sanitize_prompt(request.prompt)
        sanitized_user_id = sanitize_user_id(request.user_id)
    except SanitizationError as e:
        logger.warning(f"Input sanitization failed: {str(e)}")
        raise ValidationError(str(e))
    
    logger.info(f"Received parallel generation request from user {sanitized_user_id}")
    logger.info(f"Prompt: {sanitized_prompt[:100]}...")
    
    project = None
    
    # Step 1: Check system capacity
    can_accept, reason = resource_monitor.can_accept_new_project(
        project_manager.get_active_project_count()
    )
    
    if not can_accept:
        logger.warning(f"Cannot accept new project: {reason}")
        raise ResourceLimitError(reason)
    
    try:
        # Step 2: Create project placeholder
        project = project_manager.create_project(
            user_id=sanitized_user_id,
            prompt=sanitized_prompt
        )
        
        logger.info(f"Created project {project.id}")
        
        # Step 3: Create Expo project
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.INITIALIZING
        )
        
        logger.info("Generating unique app name")
        base_app_name = await code_generator.generate_app_name(sanitized_prompt)
        
        # Make app name unique
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        app_name = f"{base_app_name}{unique_suffix}"
        
        logger.info(f"Generated unique app name: {app_name}")
        
        # Get parent directory
        parent_dir = os.path.dirname(project.directory)
        
        # Create the Expo project
        expo_project_dir = await command_executor.create_expo_project(
            parent_dir=parent_dir,
            app_name=app_name,
            timeout=180
        )
        
        # Update project directory
        project.directory = expo_project_dir
        logger.info(f"Expo project created at {expo_project_dir}")
        
        # Step 4: Execute parallel workflow
        # This runs screen generation and tunnel creation in parallel
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.GENERATING_CODE
        )
        
        logger.info(f"Starting parallel workflow for project {project.id}")
        
        # Note: We'll start the server first, then run parallel workflow
        # Install dependencies first
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.INSTALLING_DEPS
        )
        
        logger.info(f"Installing dependencies for project {project.id}")
        await command_executor.setup_expo_project(
            project_dir=project.directory,
            port=project.port,
            timeout=300
        )
        logger.info(f"Dependencies installed for project {project.id}")
        
        # Start Expo server
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.STARTING_SERVER
        )
        
        logger.info(f"Starting Expo server for project {project.id} on port {project.port}")
        
        expo_process = await command_executor.start_expo_server(
            project_dir=project.directory,
            port=project.port
        )
        
        logger.info(f"Expo server started for project {project.id} (PID: {expo_process.pid})")
        
        # Now execute parallel workflow
        workflow_result = await parallel_workflow.execute(
            prompt=sanitized_prompt,
            project_id=project.id,
            project_dir=project.directory,
            port=project.port
        )
        
        if not workflow_result.success:
            raise Exception(f"Parallel workflow failed: {workflow_result.error}")
        
        # Update project with preview URL
        project_manager.update_preview_url(project.id, workflow_result.preview_url)
        
        logger.info(
            f"Parallel workflow completed: "
            f"tunnel={workflow_result.preview_url}, "
            f"screens={len(workflow_result.screens_created)}"
        )
        
        # Mark project as ready
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.READY
        )
        
        # Record metrics
        generation_time = time.time() - start_time
        resource_monitor.record_project_creation(generation_time)
        
        logger.info(
            f"Project {project.id} generation completed successfully in {generation_time:.2f}s"
        )
        
        return ParallelGenerateResponse(
            project_id=project.id,
            preview_url=workflow_result.preview_url,
            status="success",
            message=f"App generated with {len(workflow_result.screens_created)} screens",
            screens_created=workflow_result.screens_created,
            created_at=project.created_at.isoformat()
        )
        
    except Exception as e:
        # Handle errors
        logger.error(f"Error during parallel generation: {str(e)}", exc_info=True)
        
        if project:
            try:
                project_manager.update_project_status(
                    project.id,
                    models.project.ProjectStatus.ERROR,
                    error_message=str(e)
                )
            except Exception as status_error:
                logger.error(f"Failed to update project status: {status_error}")
        
        raise
