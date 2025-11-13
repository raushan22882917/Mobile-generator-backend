"""
AI Expo App Builder - FastAPI Backend
Main application entry point
"""
import logging
import sys
import os
import re
import asyncio
import uuid
import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError

# Fix for Windows: Set ProactorEventLoop for subprocess support
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from config import settings
from middleware.auth import verify_api_key
from middleware.rate_limit import RateLimitMiddleware
from services.code_generator import CodeGenerator
from services.project_manager import ProjectManager
from services.command_executor import CommandExecutor
from services.tunnel_manager import TunnelManager
from services.resource_monitor import ResourceMonitor
from services.cloud_storage_manager import CloudStorageManager
from utils.sanitization import sanitize_prompt, sanitize_user_id, validate_project_id, SanitizationError
import models.project
from exceptions import (
    AppBuilderError,
    AIGenerationError,
    CodeValidationError,
    DependencyInstallError,
    ServerStartError,
    TunnelCreationError,
    ResourceLimitError,
    CommandExecutionError,
    ProjectNotFoundError,
    ProjectNotReadyError,
    ArchiveCreationError,
    ValidationError
)
from models.error_response import error_from_exception

# Helper function to enhance screens with icons and images
async def enhance_screen_with_icons_and_images(
    project_id: str,
    file_path: str,
    content: str,
    project_dir: str
):
    """
    Automatically enhance a screen file with icons and generate images using Gemini
    
    Args:
        project_id: Project identifier
        file_path: Path to the screen file
        content: Current file content
        project_dir: Project directory path
    """
    import os
    from pathlib import Path
    from utils.ui_ux_principles import get_icon_for_screen, get_icon_import
    
    logger.info(f"Enhancing screen {file_path} with icons and images")
    
    # Extract screen name from file path
    screen_name = Path(file_path).stem
    
    # Get appropriate icon for this screen
    icon_mapping = get_icon_for_screen(screen_name, content[:200])  # Use first 200 chars as description
    
    # Check if @expo/vector-icons is already imported
    if "@expo/vector-icons" not in content and icon_mapping:
        # Add icon import if not present
        icon_import = get_icon_import()
        
        # Find the best place to add the import (after React imports)
        lines = content.split('\n')
        import_end_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') and 'react' in line.lower():
                import_end_index = i + 1
        
        # Insert icon import
        lines.insert(import_end_index, icon_import)
        content = '\n'.join(lines)
        
        # Update the file with enhanced content
        file_manager.write_file(project_id, file_path, content)
        logger.info(f"Added @expo/vector-icons import to {file_path}")
    
    # Generate images using Gemini if available
    if screen_generator and screen_generator.image_generator:
        try:
            # Analyze what images would be useful for this screen
            image_description = f"Professional mobile app image for {screen_name} screen. Modern, clean design suitable for React Native Expo app."
            
            # Generate image
            assets_dir = Path(project_dir) / "assets" / "images"
            assets_dir.mkdir(parents=True, exist_ok=True)
            
            image_filename = f"{screen_name.lower().replace(' ', '-')}-hero.png"
            image_path = assets_dir / image_filename
            
            generated_path = await screen_generator.image_generator.generate_image(
                prompt=image_description,
                output_path=str(image_path),
                width=800,
                height=600
            )
            
            if generated_path and os.path.exists(generated_path):
                logger.info(f"Generated image for {screen_name}: {generated_path}")
                
                # Update screen content to use the generated image
                if f"assets/images/{image_filename}" not in content:
                    # Add image import and usage
                    image_import = f"import {{ Image }} from 'react-native';"
                    if "import { Image }" not in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') and 'react-native' in line:
                                # Add Image to existing import
                                if 'Image' not in line:
                                    lines[i] = line.replace('}', ', Image }')
                                    break
                        else:
                            # Add new import
                            lines.insert(0, image_import)
                        content = '\n'.join(lines)
                    
                    # Add image usage in the component (in the return statement)
                    if f"require('@/assets/images/{image_filename}')" not in content:
                        # Try to add image in a logical place (after View opening tag)
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if '<View' in line and 'style' in line:
                                # Add image after this View
                                indent = len(line) - len(line.lstrip())
                                indent_spaces = ' ' * (indent + 2)
                                indent_spaces_inner = ' ' * (indent + 4)
                                indent_spaces_deep = ' ' * (indent + 6)
                                
                                image_code = f"{indent_spaces}<Image\n"
                                image_code += f"{indent_spaces_inner}source={{require('@/assets/images/{image_filename}')}}\n"
                                image_code += f"{indent_spaces_inner}style={{{{\n"
                                image_code += f"{indent_spaces_deep}width: '100%',\n"
                                image_code += f"{indent_spaces_deep}height: 200,\n"
                                image_code += f"{indent_spaces_deep}resizeMode: 'cover',\n"
                                image_code += f"{indent_spaces_inner}}}}}\n"
                                image_code += indent_spaces + "}/>\n"
                                lines.insert(i + 1, image_code)
                                content = '\n'.join(lines)
                                break
                        
                        # Update file with image usage
                        file_manager.write_file(project_id, file_path, content)
                        logger.info(f"Added generated image to {file_path}")
        except Exception as e:
            logger.warning(f"Failed to generate image for {screen_name}: {e}")
            # Don't fail if image generation fails

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
code_generator: CodeGenerator = None
project_manager: ProjectManager = None
command_executor: CommandExecutor = None
tunnel_manager: TunnelManager = None
resource_monitor: ResourceMonitor = None
cloud_storage_manager: CloudStorageManager = None
screen_generator = None
parallel_workflow = None
cloud_logging_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting AI Expo App Builder API...")
    
    global code_generator, project_manager, command_executor, tunnel_manager, resource_monitor, cloud_storage_manager, screen_generator, parallel_workflow, cloud_logging_service
    
    # Initialize services
    code_generator = CodeGenerator(
        api_key=settings.openai_api_key,
        model="gpt-5",
        timeout=settings.code_generation_timeout
    )
    
    project_manager = ProjectManager(
        base_dir=settings.projects_base_dir,
        max_concurrent_projects=settings.max_concurrent_projects
    )
    
    command_executor = CommandExecutor(
        default_timeout=300
    )
    
    tunnel_manager = TunnelManager(
        auth_token=settings.ngrok_auth_token,
        max_retries=3,
        retry_delay=5
    )
    
    resource_monitor = ResourceMonitor(
        max_projects=settings.max_concurrent_projects,
        max_cpu_percent=settings.max_cpu_percent,
        max_memory_percent=settings.max_memory_percent,
        min_disk_percent=settings.min_disk_percent
    )
    
    # Initialize Cloud Storage Manager (mandatory)
    cloud_storage_manager = CloudStorageManager(
        bucket_name=settings.google_cloud_bucket,
        project_id=settings.google_cloud_project
    )
    
    if not cloud_storage_manager.is_available():
        logger.error("Cloud Storage is not configured - this is required for production")
        raise RuntimeError(
            "Cloud Storage must be configured. Set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_BUCKET environment variables."
        )
    
    logger.info(f"Cloud Storage enabled: {settings.google_cloud_bucket}")
    
    # Initialize screen generator and parallel workflow
    from services.screen_generator import ScreenGenerator
    from services.parallel_workflow import ParallelWorkflow
    
    screen_generator = ScreenGenerator(
        api_key=settings.openai_api_key,
        model="gpt-5",
        gemini_api_key=settings.gemini_api_key if hasattr(settings, 'gemini_api_key') else None
    )
    
    parallel_workflow = ParallelWorkflow(
        screen_generator=screen_generator,
        tunnel_manager=tunnel_manager
    )
    
    # Initialize Cloud Logging service
    from services.cloud_logging import CloudLoggingService
    cloud_logging_service = CloudLoggingService(
        project_id=settings.google_cloud_project if settings.google_cloud_project else None,
        enabled=bool(settings.google_cloud_project)
    )
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Expo App Builder API...")
    
    # Close all tunnels
    if tunnel_manager:
        await tunnel_manager.close_all_tunnels()
    
    logger.info("Shutdown complete")


app = FastAPI(
    title="AI Expo App Builder",
    description="Generate React Native + Expo applications from natural language prompts",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
# Get allowed origins from environment variable or use defaults
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,https://mobile-generator-frontend-1098053868371.us-central1.run.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=10
)

# Include streaming generation routers
from endpoints.streaming_generate import router as streaming_router
from endpoints.fast_generate import router as fast_generate_router
from endpoints.project_endpoints import router as project_router

app.include_router(streaming_router, prefix="/api/v1", tags=["streaming"])
app.include_router(fast_generate_router, prefix="/api/v1", tags=["fast-generate"])
app.include_router(project_router, tags=["projects"])


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors
    """
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "details": exc.errors(),
            "suggestion": "Please check your request parameters and try again"
        }
    )


@app.exception_handler(AppBuilderError)
async def app_builder_exception_handler(request: Request, exc: AppBuilderError):
    """
    Handle all AppBuilder custom errors
    """
    logger.error(f"{exc.__class__.__name__}: {str(exc)}")
    
    # Create error response from exception
    error_response = error_from_exception(exc, include_details=False)
    
    # Determine HTTP status code based on error type
    if isinstance(exc, ResourceLimitError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, ProjectNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ProjectNotReadyError):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    # Create error response for unexpected errors
    error_response = error_from_exception(exc, include_details=False)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Expo App Builder API",
        "version": "1.0.0",
        "status": "running"
    }


# Request/Response Models
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GenerateRequest(BaseModel):
    """Request model for /generate endpoint"""
    prompt: str = Field(..., min_length=10, max_length=5000, description="Natural language description of the app")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")
    template_id: Optional[str] = Field(default=None, description="UI template ID to apply")


class AnalyzePromptRequest(BaseModel):
    """Request model for /analyze-prompt endpoint"""
    prompt: str = Field(..., min_length=10, max_length=5000, description="Natural language description of the app")


class GenerateResponse(BaseModel):
    """Response model for /generate endpoint"""
    project_id: str
    preview_url: Optional[str] = None
    status: str
    message: str
    created_at: str


class ProjectStatusResponse(BaseModel):
    """Response model for /status endpoint"""
    project_id: str
    status: str
    preview_url: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    last_active: str


class HealthResponse(BaseModel):
    """Response model for /health endpoint"""
    status: str
    timestamp: str
    active_projects: int
    system_metrics: Optional[dict] = None


class MetricsResponse(BaseModel):
    """Response model for /metrics endpoint"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_projects: int
    total_projects_created: int
    average_generation_time: float


class LogEntryResponse(BaseModel):
    """Response model for a single log entry"""
    timestamp: str
    severity: str
    message: str
    resource_type: str
    labels: dict


class ProjectLogsResponse(BaseModel):
    """Response model for /logs/{project_id} endpoint"""
    project_id: str
    total_logs: int
    logs: List[LogEntryResponse]
    time_range_hours: int
    cloud_logging_enabled: bool


# API Endpoints
@app.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate(request: GenerateRequest, api_key: str = Depends(verify_api_key)):
    """
    Generate a new Expo application from natural language prompt
    
    Optimized parallel workflow:
    1. Check system capacity
    2. Create Expo project immediately with basic code
    3. In parallel:
       - Setup preview (install deps + start server + create tunnel)
       - Analyze prompt for required screens
    4. After preview is ready, generate and add all screens
    
    Returns project ID and preview URL on success.
    """
    import time
    start_time = time.time()
    
    # Sanitize inputs
    try:
        sanitized_prompt = sanitize_prompt(request.prompt)
        sanitized_user_id = sanitize_user_id(request.user_id)
    except SanitizationError as e:
        logger.warning(f"Input sanitization failed: {str(e)}")
        raise ValidationError(str(e))
    
    logger.info(f"Received generation request from user {sanitized_user_id}")
    logger.info(f"Prompt: {sanitized_prompt[:100]}...")
    
    project = None
    tunnel_created = False
    
    # Step 1: Check system capacity
    can_accept, reason = resource_monitor.can_accept_new_project(
        project_manager.get_active_project_count()
    )
    
    if not can_accept:
        logger.warning(f"Cannot accept new project: {reason}")
        raise ResourceLimitError(reason)
    
    try:
        import os
        from pathlib import Path
        import random
        import string
        
        # Step 2: Create project placeholder (for tracking)
        project = project_manager.create_project(
            user_id=sanitized_user_id,
            prompt=sanitized_prompt
        )
        
        logger.info(f"Created project {project.id}")
        
        # Step 3: Create Expo project immediately with basic code
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.INITIALIZING
        )
        
        logger.info("Generating unique app name and creating Expo project")
        base_app_name = await code_generator.generate_app_name(sanitized_prompt)
        
        # Make app name unique by adding random suffix
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        app_name = f"{base_app_name}{unique_suffix}"
        
        logger.info(f"Generated unique app name: {app_name} (base: {base_app_name})")
        
        # Get parent directory (projects folder)
        parent_dir = os.path.dirname(project.directory)
        
        # Create the Expo project
        expo_project_dir = await command_executor.create_expo_project(
            parent_dir=parent_dir,
            app_name=app_name,
            timeout=180
        )
        
        # Update project directory to the created expo project
        project.directory = expo_project_dir
        logger.info(f"Expo project created at {expo_project_dir}")
        
        # Step 4: Generate basic initial code and write it
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.GENERATING_CODE
        )
        
        logger.info(f"Generating initial code for project {project.id}")
        generated_code = await code_generator.generate_app_code(sanitized_prompt)
        logger.info(f"Initial code generated successfully for project {project.id}")
        
        # Apply template if specified
        if request.template_id:
            logger.info(f"Applying template {request.template_id} to generated code")
            from templates.ui_templates import get_template, apply_template_to_code, generate_template_stylesheet
            
            template = get_template(request.template_id)
            if template:
                # Apply template to generated code
                for code_file in generated_code.files:
                    code_file.content = apply_template_to_code(code_file.content, template)
                
                logger.info(f"Template {template.name} applied successfully")
            else:
                logger.warning(f"Template {request.template_id} not found, skipping")
        
        # Write initial code files
        logger.info(f"Writing initial code to project {project.id}")
        project_manager.write_code_files(project, generated_code)
        
        # Write template stylesheet if template was applied
        if request.template_id:
            template = get_template(request.template_id)
            if template:
                from templates.ui_templates import generate_template_stylesheet
                stylesheet_content = generate_template_stylesheet(template)
                stylesheet_path = os.path.join(project.directory, "theme.ts")
                with open(stylesheet_path, 'w', encoding='utf-8') as f:
                    f.write(stylesheet_content)
                logger.info(f"Template stylesheet written to theme.ts")
        
        logger.info(f"Initial code files written for project {project.id}")
        
        # Step 5: Run preview setup and screen analysis in parallel
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.INSTALLING_DEPS
        )
        
        async def setup_preview():
            """Setup preview: install deps, start server, create tunnel"""
            logger.info(f"Setting up preview for project {project.id}")
            
            # Install dependencies
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
            
            # Create tunnel
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.CREATING_TUNNEL
            )
            
            logger.info(f"Creating tunnel for project {project.id}")
            preview_url = await tunnel_manager.create_tunnel(
                port=project.port,
                project_id=project.id
            )
            logger.info(f"Tunnel created for project {project.id}: {preview_url}")
            
            return preview_url
        
        async def analyze_screens():
            """Analyze prompt to determine required screens"""
            logger.info(f"Analyzing prompt for required screens for project {project.id}")
            if screen_generator:
                try:
                    suggestions = await screen_generator.analyze_prompt_suggestions(sanitized_prompt)
                    logger.info(f"Screen analysis complete: {suggestions.get('total_screens', 0)} screens needed")
                    return suggestions
                except Exception as e:
                    logger.warning(f"Screen analysis failed: {e}, continuing without additional screens")
                    return None
            return None
        
        # Run preview setup and screen analysis in parallel
        logger.info(f"Starting parallel execution: preview setup + screen analysis")
        preview_url, screen_suggestions = await asyncio.gather(
            setup_preview(),
            analyze_screens()
        )
        
        tunnel_created = True
        project_manager.update_preview_url(project.id, preview_url)
        
        # Step 6: After preview is ready, generate and add all required screens
        if screen_suggestions and screen_suggestions.get('total_screens', 0) > 0:
            logger.info(f"Generating {screen_suggestions['total_screens']} additional screens for project {project.id}")
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.GENERATING_CODE
            )
            
            try:
                # Generate all screens
                screen_definitions = await screen_generator.analyze_and_generate_screens(
                    sanitized_prompt,
                    generate_images=True
                )
                
                # Write screens to project
                if screen_definitions:
                    loop = asyncio.get_event_loop()
                    created_files = await loop.run_in_executor(
                        None,
                        screen_generator.write_screens_to_project,
                        screen_definitions,
                        project.directory
                    )
                    logger.info(f"Added {len(created_files)} screens to project {project.id}")
                    
                    # Generate images for screens in background (non-blocking)
                    if screen_generator.image_generator:
                        asyncio.create_task(
                            screen_generator.generate_images_for_project(
                                screen_definitions,
                                project.directory
                            )
                        )
                        logger.info(f"Image generation started in background for project {project.id}")
            except Exception as e:
                logger.warning(f"Failed to add additional screens: {e}, continuing with basic app")
        
        # Step 7: Mark project as ready
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
        
        return GenerateResponse(
            project_id=project.id,
            preview_url=preview_url,
            status="success",
            message="App generated successfully",
            created_at=project.created_at.isoformat()
        )
        
    except Exception as e:
        # Handle all errors with proper cleanup
        logger.error(f"Error during generation: {str(e)}", exc_info=True)
        
        # Update project status if project was created
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
        
    finally:
        # Don't cleanup - keep projects for debugging and reuse
        if project and project.status == models.project.ProjectStatus.ERROR:
            logger.info(f"Project {project.id} failed but keeping files for debugging")
            
            # Close tunnel if it was created
            if tunnel_created:
                try:
                    await tunnel_manager.close_tunnel(project.id)
                    logger.info(f"Tunnel closed for failed project {project.id}")
                except Exception as tunnel_error:
                    logger.error(f"Failed to close tunnel: {tunnel_error}")


@app.get("/status/{project_id}", response_model=ProjectStatusResponse)
async def get_status(project_id: str):
    """
    Get current status of a project generation
    
    Returns project status, preview URL (if ready), and error information (if failed).
    This endpoint is used by the frontend to poll for progress updates.
    """
    # Validate project ID
    try:
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {project_id}")
        raise ValidationError(str(e))
    
    logger.debug(f"Status check for project {validated_project_id}")
    
    # Get project from manager
    project = project_manager.get_project(validated_project_id)
    
    if not project:
        logger.warning(f"Status requested for non-existent project: {project_id}")
        raise ProjectNotFoundError(project_id)
    
    return ProjectStatusResponse(
        project_id=project.id,
        status=project.status.value,
        preview_url=project.preview_url,
        error=project.error_message,
        created_at=project.created_at.isoformat(),
        last_active=project.last_active.isoformat()
    )


@app.get("/project-status/{project_id}")
async def get_project_status(project_id: str):
    """
    Alias for /status/{project_id} - Get current status of a project
    Returns simplified status information for terminal display
    """
    try:
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {project_id}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    
    project = project_manager.get_project(validated_project_id)
    
    if not project:
        return JSONResponse(status_code=404, content={"error": "Project not found"})
    
    return {
        "status": project.status.value,
        "port": project.port if hasattr(project, 'port') else None,
        "url": project.preview_url,
        "project_id": project.id
    }


@app.get("/logs/{project_id}", response_model=ProjectLogsResponse)
async def get_project_logs(
    project_id: str,
    hours: int = 24,
    limit: int = 1000,
    severity: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Get Google Cloud logs for a specific project
    
    Fetches logs from Google Cloud Logging API including:
    - Cloud Run service logs
    - Cloud Build logs
    - Any logs related to the project
    
    Args:
        project_id: Project identifier
        hours: Number of hours to look back (default: 24, max: 168)
        limit: Maximum number of log entries to return (default: 1000, max: 10000)
        severity: Filter by severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        ProjectLogsResponse with log entries from Google Cloud
    """
    # Validate project ID
    try:
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {project_id}")
        raise ValidationError(str(e))
    
    # Validate parameters
    hours = max(1, min(hours, 168))  # Limit to 1-168 hours (1 week)
    limit = max(1, min(limit, 10000))  # Limit to 1-10000 entries
    
    logger.info(
        f"Logs requested for project {validated_project_id} "
        f"(hours: {hours}, limit: {limit}, severity: {severity})"
    )
    
    # Check if project exists
    project = project_manager.get_project(validated_project_id)
    if not project:
        logger.warning(f"Logs requested for non-existent project: {project_id}")
        raise ProjectNotFoundError(project_id)
    
    # Check if Cloud Logging is enabled
    if not cloud_logging_service or not cloud_logging_service.enabled:
        logger.warning("Cloud Logging not enabled or not configured")
        return ProjectLogsResponse(
            project_id=validated_project_id,
            total_logs=0,
            logs=[],
            time_range_hours=hours,
            cloud_logging_enabled=False
        )
    
    try:
        # Fetch logs from Google Cloud
        log_entries = cloud_logging_service.get_project_logs(
            project_id=validated_project_id,
            hours=hours,
            limit=limit,
            severity=severity
        )
        
        # Convert to response format
        log_responses = [
            LogEntryResponse(
                timestamp=entry.timestamp,
                severity=entry.severity,
                message=entry.message,
                resource_type=entry.resource_type,
                labels=entry.labels
            )
            for entry in log_entries
        ]
        
        logger.info(
            f"Retrieved {len(log_responses)} log entries for project {validated_project_id}"
        )
        
        return ProjectLogsResponse(
            project_id=validated_project_id,
            total_logs=len(log_responses),
            logs=log_responses,
            time_range_hours=hours,
            cloud_logging_enabled=True
        )
        
    except Exception as e:
        logger.error(f"Error fetching logs for project {validated_project_id}: {str(e)}", exc_info=True)
        raise AIGenerationError(
            f"Failed to fetch logs: {str(e)}",
            "Please check Google Cloud Logging configuration"
        )


@app.get("/download/{project_id}")
async def download_project(project_id: str, background_tasks: BackgroundTasks):
    """
    Download project as ZIP archive
    
    Creates a ZIP archive of the project (excluding node_modules and build artifacts)
    and returns it as a file download. The archive is automatically cleaned up after
    download.
    """
    # Validate project ID
    try:
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {project_id}")
        raise ValidationError(str(e))
    
    logger.info(f"Download requested for project {validated_project_id}")
    
    # Get project from manager
    project = project_manager.get_project(validated_project_id)
    
    if not project:
        logger.warning(f"Download requested for non-existent project: {project_id}")
        raise ProjectNotFoundError(project_id)
    
    # Check if project is ready
    if project.status != models.project.ProjectStatus.READY:
        logger.warning(f"Download requested for project {project_id} with status {project.status.value}")
        raise ProjectNotReadyError(project_id, project.status.value)
    
    try:
        # Create archive
        archive_path = project_manager.archive_project(project_id)
        logger.info(f"Archive created for project {project_id}: {archive_path}")
        
        # Schedule cleanup of archive file after download
        def cleanup_archive():
            """Delete archive file after download"""
            try:
                import os
                if os.path.exists(archive_path):
                    os.remove(archive_path)
                    logger.info(f"Cleaned up archive: {archive_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup archive {archive_path}: {e}")
        
        background_tasks.add_task(cleanup_archive)
        
        # Return file response
        return FileResponse(
            path=archive_path,
            media_type="application/zip",
            filename=f"expo-app-{project_id[:8]}.zip",
            headers={
                "Content-Disposition": f"attachment; filename=expo-app-{project_id[:8]}.zip"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create archive for project {project_id}: {str(e)}")
        raise ArchiveCreationError(f"Failed to create project archive: {str(e)}")


@app.get("/files/{project_id}")
async def get_project_files(project_id: str):
    """
    Get project file tree structure
    
    Returns the file tree of the project with file contents for preview
    """
    # Validate project ID
    try:
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {project_id}")
        raise ValidationError(str(e))
    
    logger.info(f"File tree requested for project {validated_project_id}")
    
    # Get project from manager
    project = project_manager.get_project(validated_project_id)
    
    if not project:
        logger.warning(f"File tree requested for non-existent project: {project_id}")
        raise ProjectNotFoundError(project_id)
    
    try:
        import os
        from pathlib import Path
        
        def build_file_tree(directory: str, base_path: str = "") -> list:
            """Build file tree structure"""
            items = []
            try:
                for item in sorted(os.listdir(directory)):
                    # Skip node_modules, .expo, and other build artifacts
                    if item in ['node_modules', '.expo', '.git', 'dist', 'build', '__pycache__']:
                        continue
                    
                    item_path = os.path.join(directory, item)
                    relative_path = os.path.join(base_path, item) if base_path else item
                    
                    if os.path.isdir(item_path):
                        # Folder
                        items.append({
                            "name": item,
                            "type": "folder",
                            "path": relative_path,
                            "children": build_file_tree(item_path, relative_path)
                        })
                    else:
                        # File - read content for small files
                        content = None
                        try:
                            file_size = os.path.getsize(item_path)
                            # Only read files smaller than 100KB
                            if file_size < 100 * 1024:
                                with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                        except:
                            content = "// Unable to read file"
                        
                        items.append({
                            "name": item,
                            "type": "file",
                            "path": relative_path,
                            "content": content
                        })
            except Exception as e:
                logger.error(f"Error reading directory {directory}: {e}")
            
            return items
        
        file_tree = build_file_tree(project.directory)
        
        return {
            "project_id": project_id,
            "file_tree": file_tree
        }
        
    except Exception as e:
        logger.error(f"Failed to get file tree for project {project_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to retrieve file tree", "details": str(e)}
        )


@app.get("/projects")
async def list_projects():
    """
    List all projects in the projects folder
    
    Returns a list of all projects with their metadata
    """
    logger.info("Projects list requested")
    
    try:
        import os
        from pathlib import Path
        from datetime import datetime
        
        projects_dir = Path(settings.projects_base_dir)
        
        if not projects_dir.exists():
            return {"projects": []}
        
        projects_list = []
        
        # Scan projects directory
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            
            project_id = project_dir.name
            
            # Get project from active projects or read from disk
            project = project_manager.get_project(project_id)
            
            if project:
                # Active project
                projects_list.append({
                    "id": project.id,
                    "name": project_id,
                    "status": project.status.value,
                    "preview_url": project.preview_url,
                    "preview_urls": project.preview_urls,
                    "created_at": project.created_at.isoformat(),
                    "last_active": project.last_active.isoformat(),
                    "prompt": project.prompt[:100] + "..." if len(project.prompt) > 100 else project.prompt,
                    "is_active": True
                })
            else:
                # Inactive project - read metadata from disk
                try:
                    # Check if package.json exists
                    package_json = project_dir / "package.json"
                    if package_json.exists():
                        # Get creation time
                        created_time = datetime.fromtimestamp(os.path.getctime(str(project_dir)))
                        modified_time = datetime.fromtimestamp(os.path.getmtime(str(project_dir)))
                        
                        projects_list.append({
                            "id": project_id,
                            "name": project_id,
                            "status": "inactive",
                            "preview_url": None,
                            "preview_urls": [],
                            "created_at": created_time.isoformat(),
                            "last_active": modified_time.isoformat(),
                            "prompt": "Project created previously",
                            "is_active": False
                        })
                except Exception as e:
                    logger.warning(f"Error reading project {project_id}: {e}")
                    continue
        
        # Sort by last_active (most recent first)
        projects_list.sort(key=lambda x: x["last_active"], reverse=True)
        
        logger.info(f"Found {len(projects_list)} projects")
        
        return {
            "projects": projects_list,
            "total": len(projects_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to list projects", "details": str(e)}
        )


@app.post("/analyze-prompt")
async def analyze_prompt(request: AnalyzePromptRequest, api_key: str = Depends(verify_api_key)):
    """
    Analyze a prompt and return suggested screens and images WITHOUT generating the project
    
    This endpoint helps users preview what will be created before committing to generation.
    Returns:
    - List of suggested screens with descriptions
    - List of suggested images with descriptions
    - Total counts
    """
    try:
        # Sanitize input
        sanitized_prompt = sanitize_prompt(request.prompt)
        logger.info(f"Analyzing prompt: {sanitized_prompt[:100]}...")
        
        # Use screen generator to analyze
        if not screen_generator:
            raise AppBuilderError("Screen generator not initialized")
        
        suggestions = await screen_generator.analyze_prompt_suggestions(sanitized_prompt)
        
        logger.info(f"Analysis complete: {suggestions['total_screens']} screens, {suggestions['total_images']} images")
        
        return {
            "success": True,
            "suggestions": suggestions,
            "message": f"Found {suggestions['total_screens']} screens and {suggestions['total_images']} images"
        }
        
    except SanitizationError as e:
        logger.warning(f"Input sanitization failed: {str(e)}")
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Failed to analyze prompt: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to analyze prompt", "details": str(e)}
        )


@app.post("/projects/{project_id}/activate")
async def activate_project(project_id: str):
    """
    Activate an inactive project by starting its server and creating a tunnel
    
    This endpoint allows users to reopen previously created projects
    """
    # Validate project ID
    try:
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {project_id}")
        raise ValidationError(str(e))
    
    logger.info(f"Activation requested for project {validated_project_id}")
    
    try:
        # Check if project is already active and ready
        existing_project = project_manager.get_project(validated_project_id)
        
        if existing_project and existing_project.id in project_manager.active_projects:
            # If project is in error state, allow reactivation by removing it first
            if existing_project.status == models.project.ProjectStatus.ERROR:
                logger.info(f"Project {validated_project_id} is in error state, removing from active projects for reactivation")
                # Release the port and remove from active projects
                project_manager.port_manager.release_port(existing_project.port)
                del project_manager.active_projects[validated_project_id]
            elif existing_project.status == models.project.ProjectStatus.READY:
                # Already active and ready - just return current status
                logger.info(f"Project {validated_project_id} is already active and ready")
                return {
                    "project_id": existing_project.id,
                    "status": existing_project.status.value,
                    "preview_url": existing_project.preview_url,
                    "message": "Project is already active"
                }
            else:
                # Project is in progress (starting, generating, etc.)
                logger.info(f"Project {validated_project_id} is already being processed")
                return {
                    "project_id": existing_project.id,
                    "status": existing_project.status.value,
                    "preview_url": existing_project.preview_url,
                    "message": "Project is currently being processed"
                }
        
        # Reactivate the project
        project = project_manager.reactivate_project(validated_project_id)
        
        # Update status to installing dependencies
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.INSTALLING_DEPS
        )
        
        # Ensure dependencies are installed before starting server
        logger.info(f"Setting up Expo project for {project.id} in {project.directory}")
        try:
            await asyncio.wait_for(
                command_executor.setup_expo_project(
                    project_dir=project.directory,
                    port=project.port,
                    timeout=600  # 10 minutes for npm install
                ),
                timeout=600  # 10 minutes timeout
            )
            logger.info(f"Dependencies installed successfully for project {project.id}")
        except asyncio.TimeoutError:
            logger.error(f"Dependency installation timed out for project {project.id}")
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message="Dependency installation timed out after 10 minutes"
            )
            raise DependencyInstallError("Dependency installation timed out")
        except CommandExecutionError as e:
            error_msg = f"Failed to install dependencies: {str(e)}"
            logger.error(error_msg)
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message=error_msg
            )
            raise DependencyInstallError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error installing dependencies: {str(e)}"
            logger.error(error_msg, exc_info=True)
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message=str(e)
            )
            raise
        
        # Update status to starting server
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.STARTING_SERVER
        )
        
        # Start Expo server with timeout handling
        logger.info(f"Starting Expo server for reactivated project {project.id} on port {project.port}")
        try:
            expo_process = await asyncio.wait_for(
                command_executor.start_expo_server(
                    project_dir=project.directory,
                    port=project.port
                ),
                timeout=90  # 90 second timeout for server start
            )
            logger.info(f"Expo server started for project {project.id} (PID: {expo_process.pid})")
        except asyncio.TimeoutError:
            logger.error(f"Expo server start timed out for project {project.id}")
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message="Server start timed out after 90 seconds"
            )
            raise ServerStartError("Expo server failed to start within 90 seconds")
        except CommandExecutionError as e:
            error_msg = f"Failed to start Expo server: {str(e)}"
            logger.error(error_msg)
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message=error_msg
            )
            raise ServerStartError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error starting Expo server: {str(e)}"
            logger.error(error_msg, exc_info=True)
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message=str(e)
            )
            raise
        
        # Create tunnel
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.CREATING_TUNNEL
        )
        
        logger.info(f"Creating tunnel for reactivated project {project.id}")
        try:
            preview_url = await asyncio.wait_for(
                tunnel_manager.create_tunnel(
                    port=project.port,
                    project_id=project.id
                ),
                timeout=30  # 30 second timeout for tunnel creation
            )
            
            project_manager.update_preview_url(project.id, preview_url)
            logger.info(f"Tunnel created for project {project.id}: {preview_url}")
        except asyncio.TimeoutError:
            logger.error(f"Tunnel creation timed out for project {project.id}")
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message="Tunnel creation timed out"
            )
            raise TunnelCreationError("Failed to create tunnel within 30 seconds")
        except Exception as e:
            logger.error(f"Failed to create tunnel: {e}")
            project_manager.update_project_status(
                project.id,
                models.project.ProjectStatus.ERROR,
                error_message=str(e)
            )
            raise
        
        # Mark as ready
        project_manager.update_project_status(
            project.id,
            models.project.ProjectStatus.READY
        )
        
        logger.info(f"Project {project.id} reactivated successfully")
        
        return {
            "project_id": project.id,
            "status": "ready",
            "preview_url": preview_url,
            "message": "Project activated successfully"
        }
        
    except ValueError as e:
        error_msg = f"Failed to activate project {validated_project_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ProjectNotFoundError(validated_project_id)
    except (ProjectNotFoundError, DependencyInstallError, ServerStartError, TunnelCreationError) as e:
        # Re-raise known exceptions as-is (they're already properly handled)
        raise
    except Exception as e:
        error_msg = f"Unexpected error activating project {validated_project_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Clean up project if it was added to active projects
        try:
            if validated_project_id in project_manager.active_projects:
                project = project_manager.active_projects[validated_project_id]
                if hasattr(project, 'port'):
                    project_manager.port_manager.release_port(project.port)
                del project_manager.active_projects[validated_project_id]
                logger.info(f"Cleaned up project {validated_project_id} after error")
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup project {validated_project_id}: {cleanup_error}")
        raise ServerStartError(error_msg)


class ManualActivateRequest(BaseModel):
    """Request model for manual activation"""
    preview_url: str = Field(..., description="Manually provided preview URL (ngrok or other)")


@app.post("/projects/{project_id}/manual-activate")
async def manual_activate_project(project_id: str, request: ManualActivateRequest):
    """
    Manually activate a project by providing the preview URL directly
    
    This is useful when automated activation fails. You can:
    1. Manually start the Expo server (npx expo start --port XXXX)
    2. Manually create ngrok tunnel (ngrok http XXXX)
    3. Call this endpoint with the ngrok URL
    """
    # Validate project ID
    try:
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {project_id}")
        raise ValidationError(str(e))
    
    logger.info(f"Manual activation requested for project {validated_project_id}")
    logger.info(f"Preview URL: {request.preview_url}")
    
    # Get or load project
    project = project_manager.get_project(validated_project_id)
    
    if not project:
        raise ProjectNotFoundError(validated_project_id)
    
    # If not in active projects, add it
    if validated_project_id not in project_manager.active_projects:
        # Allocate a port (even though we're not using it for automated start)
        port = project_manager.port_manager.allocate_port()
        project.port = port
        project_manager.active_projects[validated_project_id] = project
        logger.info(f"Added project {validated_project_id} to active projects")
    
    # Update preview URL
    project_manager.update_preview_url(validated_project_id, request.preview_url)
    
    # Mark as ready
    project_manager.update_project_status(
        validated_project_id,
        models.project.ProjectStatus.READY
    )
    
    logger.info(f"Project {validated_project_id} manually activated successfully")
    
    return {
        "project_id": validated_project_id,
        "status": "ready",
        "preview_url": request.preview_url,
        "message": "Project manually activated successfully"
    }


@app.get("/templates")
async def get_templates():
    """
    Get all available UI templates
    
    Returns a list of all available color schemes and UI templates
    """
    try:
        from templates.ui_templates import get_all_templates
        
        templates = get_all_templates()
        
        return {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "colors": {
                        "primary": t.colors.primary,
                        "secondary": t.colors.secondary,
                        "accent": t.colors.accent,
                        "background": t.colors.background,
                        "surface": t.colors.surface,
                        "text_primary": t.colors.text_primary,
                        "text_secondary": t.colors.text_secondary,
                        "border": t.colors.border if hasattr(t.colors, 'border') else t.colors.surface,
                    },
                    "preview_image": t.preview_image if hasattr(t, 'preview_image') else None,
                    "preview_url": f"/template-preview/{t.id}"
                }
                for t in templates
            ]
        }
    except Exception as e:
        logger.error(f"Error loading templates: {e}", exc_info=True)
        # Return empty list instead of error to prevent frontend crash
        return {"templates": []}


@app.get("/template-preview/{template_id}")
async def get_template_preview(template_id: str):
    """
    Get HTML preview of a template
    
    Returns an HTML page showing the template with dummy data
    """
    import os
    from fastapi.responses import HTMLResponse
    
    # Check if HTML preview exists
    html_path = os.path.join("templates", "html", f"{template_id}.html")
    
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    # If no HTML file, generate a simple preview
    from templates.ui_templates import get_template
    template = get_template(template_id)
    
    if not template:
        return HTMLResponse(content="<h1>Template not found</h1>", status_code=404)
    
    # Generate simple HTML preview
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{template.name} Preview</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: {template.colors.background};
                color: {template.colors.text_primary};
                padding: 20px;
                margin: 0;
            }}
            .container {{
                max-width: 400px;
                margin: 0 auto;
                background: {template.colors.surface};
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            h1 {{ color: {template.colors.primary}; }}
            .button {{
                background: {template.colors.primary};
                color: {template.colors.surface};
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                margin: 8px 0;
                width: 100%;
            }}
            .card {{
                background: {template.colors.background};
                border: 1px solid {template.colors.border};
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{template.name}</h1>
            <p style="color: {template.colors.text_secondary}">{template.description}</p>
            <div class="card">
                <h3 style="color: {template.colors.secondary}">Sample Card</h3>
                <p>This is how your app will look with this template.</p>
            </div>
            <button class="button">Primary Button</button>
            <button class="button" style="background: {template.colors.secondary}">Secondary Button</button>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


class ApplyTemplateRequest(BaseModel):
    """Request model for applying template to existing project"""
    project_id: str
    template_id: str


@app.post("/apply-template")
async def apply_template(request: ApplyTemplateRequest, api_key: str = Depends(verify_api_key)):
    """
    Apply a UI template to an existing project
    
    Updates all code files with the selected template's colors and styles
    """
    try:
        validated_project_id = validate_project_id(request.project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {request.project_id}")
        raise ValidationError(str(e))
    
    logger.info(f"Applying template {request.template_id} to project {validated_project_id}")
    
    # Get project
    project = project_manager.get_project(validated_project_id)
    if not project:
        logger.warning(f"Template application for non-existent project: {validated_project_id}")
        raise ProjectNotFoundError(validated_project_id)
    
    try:
        from templates.ui_templates import get_template, apply_template_to_code, generate_template_stylesheet
        from pathlib import Path
        
        template = get_template(request.template_id)
        if not template:
            return JSONResponse(
                status_code=400,
                content={"error": f"Template '{request.template_id}' not found"}
            )
        
        # Find and update all code files
        project_path = Path(project.directory)
        files_updated = []
        
        for file_path in project_path.rglob("*.tsx"):
            if "node_modules" not in str(file_path) and ".expo" not in str(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Apply template
                    updated_content = apply_template_to_code(content, template)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    relative_path = file_path.relative_to(project_path)
                    files_updated.append(str(relative_path))
                    logger.info(f"Applied template to {relative_path}")
                except Exception as e:
                    logger.warning(f"Could not update {file_path}: {e}")
        
        for file_path in project_path.rglob("*.ts"):
            if "node_modules" not in str(file_path) and ".expo" not in str(file_path) and "theme.ts" not in str(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Apply template
                    updated_content = apply_template_to_code(content, template)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    relative_path = file_path.relative_to(project_path)
                    files_updated.append(str(relative_path))
                    logger.info(f"Applied template to {relative_path}")
                except Exception as e:
                    logger.warning(f"Could not update {file_path}: {e}")
        
        # Write/update template stylesheet
        stylesheet_content = generate_template_stylesheet(template)
        stylesheet_path = project_path / "theme.ts"
        with open(stylesheet_path, 'w', encoding='utf-8') as f:
            f.write(stylesheet_content)
        files_updated.append("theme.ts")
        
        logger.info(f"Template {template.name} applied to {len(files_updated)} files")
        
        # Trigger Metro reload
        file_manager._trigger_reload(validated_project_id)
        
        return {
            "success": True,
            "template": template.name,
            "files_updated": files_updated,
            "message": f"Applied {template.name} template to {len(files_updated)} files"
        }
        
    except Exception as e:
        logger.error(f"Error applying template: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to apply template: {str(e)}"}
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancers
    
    Returns basic health status and optionally system metrics.
    This endpoint should respond quickly (< 2 seconds) for load balancer health checks.
    """
    try:
        active_projects = project_manager.get_active_project_count()
        
        # Get basic system metrics
        metrics = resource_monitor.get_system_metrics(active_projects)
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            active_projects=active_projects,
            system_metrics={
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_percent": metrics.disk_percent
            }
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        # Return degraded status but still 200 OK
        return HealthResponse(
            status="degraded",
            timestamp=datetime.now().isoformat(),
            active_projects=0,
            system_metrics=None
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint
    
    Returns detailed system metrics including:
    - CPU usage
    - Memory usage
    - Disk usage
    - Active projects count
    - Total projects created
    - Average generation time
    """
    try:
        active_projects = project_manager.get_active_project_count()
        metrics = resource_monitor.get_system_metrics(active_projects)
        
        return MetricsResponse(
            cpu_percent=metrics.cpu_percent,
            memory_percent=metrics.memory_percent,
            disk_percent=metrics.disk_percent,
            active_projects=metrics.active_projects,
            total_projects_created=metrics.total_projects_created,
            average_generation_time=metrics.average_generation_time
        )
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "METRICS_ERROR",
                "message": f"Failed to retrieve metrics: {str(e)}"
            }
        )


class ChatEditRequest(BaseModel):
    """Request model for /chat/edit endpoint"""
    project_id: str = Field(..., description="Project ID to edit")
    prompt: str = Field(..., min_length=10, max_length=2000, description="Natural language instruction for editing")


class ChatEditResponse(BaseModel):
    """Response model for /chat/edit endpoint"""
    success: bool
    message: str
    files_modified: list[str]
    changes_summary: str


@app.post("/chat/edit", response_model=ChatEditResponse)
async def chat_edit(request: ChatEditRequest, api_key: str = Depends(verify_api_key)):
    """
    AI-powered file editing through chat
    
    This endpoint allows users to describe changes they want to make,
    and the AI will analyze the project and update the relevant files.
    """
    try:
        # Validate project ID
        validated_project_id = validate_project_id(request.project_id)
    except SanitizationError as e:
        logger.warning(f"Invalid project ID: {request.project_id}")
        raise ValidationError(str(e))
    
    # Sanitize prompt
    try:
        sanitized_prompt = sanitize_prompt(request.prompt)
    except SanitizationError as e:
        logger.warning(f"Input sanitization failed: {str(e)}")
        raise ValidationError(str(e))
    
    logger.info(f"Chat edit request for project {validated_project_id}: {sanitized_prompt[:100]}...")
    
    # Get project
    project = project_manager.get_project(validated_project_id)
    if not project:
        logger.warning(f"Edit requested for non-existent project: {validated_project_id}")
        raise ProjectNotFoundError(validated_project_id)
    
    try:
        import os
        from pathlib import Path
        
        # Read current project files
        project_files = {}
        project_path = Path(project.directory)
        
        # Read key files (App.tsx, components, etc.)
        for file_path in project_path.rglob("*.tsx"):
            if "node_modules" not in str(file_path) and ".expo" not in str(file_path):
                relative_path = file_path.relative_to(project_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        project_files[str(relative_path)] = f.read()
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")
        
        for file_path in project_path.rglob("*.ts"):
            if "node_modules" not in str(file_path) and ".expo" not in str(file_path):
                relative_path = file_path.relative_to(project_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        project_files[str(relative_path)] = f.read()
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")
        
        # Extract file mentions from prompt (files mentioned with @)
        import re
        mentioned_files = re.findall(r'@([\w\./\-]+(?:\.\w+)?)', sanitized_prompt)
        
        # If specific files are mentioned, focus on those
        if mentioned_files:
            # Filter to only mentioned files
            focused_files = {
                path: content 
                for path, content in project_files.items() 
                if any(mentioned in path for mentioned in mentioned_files)
            }
            
            if focused_files:
                project_files = focused_files
                logger.info(f"Focusing on mentioned files: {list(focused_files.keys())}")
        
        # Build context for AI
        files_context = "\n\n".join([
            f"// FILE: {path}\n{content[:3000]}" 
            for path, content in list(project_files.items())[:15]  # Limit to first 15 files
        ])
        
        # Create AI prompt for editing
        if mentioned_files:
            file_instruction = f"\nFocus on these specific files: {', '.join(mentioned_files)}"
        else:
            file_instruction = ""
        
        edit_prompt = f"""You are an expert React Native developer. Analyze the project files and make the requested changes.

Current Project Files:
{files_context}

User Request:
{sanitized_prompt}{file_instruction}

Instructions:
1. Analyze which files need to be modified or created
2. Generate the complete updated content for each file
3. If the user wants to create new screens/components, use CREATE instead of EDIT
4. Ensure all changes are compatible with React Native and Expo
5. Maintain existing code style and structure
6. If specific files are mentioned with @, focus your changes on those files
7. Keep all existing imports and dependencies unless they need to change
8. For new screens, follow the project structure (app/ for screens, components/ for reusable components)

Output Format:
For existing files that need changes:
// EDIT: <filepath>
<complete updated file content>
// END_EDIT

For new files to create:
// CREATE: <filepath>
<complete new file content>
// END_CREATE

Examples:
- To edit: // EDIT: app/index.tsx
- To create new screen: // CREATE: app/profile.tsx
- To create component: // CREATE: components/Button.tsx

Provide a brief summary of changes at the end starting with "SUMMARY:"
"""
        
        # Call AI to generate edits
        logger.info("Generating file edits with AI")
        response = await asyncio.wait_for(
            code_generator.client.responses.create(
                model=code_generator.model,
                input=edit_prompt
            ),
            timeout=120
        )
        
        ai_response = response.output_text
        
        # Parse AI response to extract file edits and creates
        files_modified = []
        files_created = []
        current_file = None
        current_content = []
        current_action = None  # 'edit' or 'create'
        summary = ""
        
        for line in ai_response.split('\n'):
            if line.startswith('// EDIT:') or line.startswith('// CREATE:'):
                # Start of new file operation
                if current_file and current_content:
                    # Save previous file
                    file_path = project_path / current_file
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(current_content))
                    
                    if current_action == 'create':
                        files_created.append(current_file)
                        logger.info(f"Created file: {current_file}")
                    else:
                        files_modified.append(current_file)
                        logger.info(f"Updated file: {current_file}")
                
                if line.startswith('// EDIT:'):
                    current_file = line.replace('// EDIT:', '').strip()
                    current_action = 'edit'
                else:
                    current_file = line.replace('// CREATE:', '').strip()
                    current_action = 'create'
                current_content = []
                
            elif line.startswith('// END_EDIT') or line.startswith('// END_CREATE'):
                # End of file operation
                if current_file and current_content:
                    file_path = project_path / current_file
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(current_content))
                    
                    if current_action == 'create':
                        files_created.append(current_file)
                        logger.info(f"Created file: {current_file}")
                    else:
                        files_modified.append(current_file)
                        logger.info(f"Updated file: {current_file}")
                        
                current_file = None
                current_content = []
                current_action = None
            elif line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
            elif current_file:
                current_content.append(line)
        
        # Handle last file if no END marker
        if current_file and current_content:
            file_path = project_path / current_file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(current_content))
            
            if current_action == 'create':
                files_created.append(current_file)
                logger.info(f"Created file: {current_file}")
            else:
                files_modified.append(current_file)
                logger.info(f"Updated file: {current_file}")
        
        all_files = files_modified + files_created
        if not all_files:
            return ChatEditResponse(
                success=False,
                message="No files were modified or created. The AI couldn't determine what changes to make.",
                files_modified=[],
                changes_summary="No changes made"
            )
        
        # Trigger Metro reload
        file_manager._trigger_reload(validated_project_id)
        
        logger.info(f"Successfully modified {len(files_modified)} and created {len(files_created)} files for project {validated_project_id}")
        
        result_message = []
        if files_modified:
            result_message.append(f"Updated {len(files_modified)} file(s)")
        if files_created:
            result_message.append(f"Created {len(files_created)} file(s)")
        
        return ChatEditResponse(
            success=True,
            message=" and ".join(result_message),
            files_modified=all_files,
            changes_summary=summary or f"{' and '.join(result_message)} based on your request"
        )
        
    except asyncio.TimeoutError:
        logger.error("AI edit generation timed out")
        raise AIGenerationError("Edit generation timed out", "Please try with a simpler request")
    except Exception as e:
        logger.error(f"Error during chat edit: {str(e)}", exc_info=True)
        raise AIGenerationError(f"Failed to process edit: {str(e)}", "Please try again")


@app.websocket("/ws/watch/{project_id}")
async def websocket_watch_files(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time file change notifications
    
    Watches project files and sends notifications when changes are detected
    """
    await websocket.accept()
    
    try:
        # Validate project ID
        validated_project_id = validate_project_id(project_id)
    except SanitizationError as e:
        await websocket.close(code=1008, reason=f"Invalid project ID: {str(e)}")
        return
    
    # Get project
    project = project_manager.get_project(validated_project_id)
    if not project:
        await websocket.close(code=1008, reason="Project not found")
        return
    
    logger.info(f"WebSocket file watcher connected for project {validated_project_id}")
    
    try:
        import os
        import time
        from pathlib import Path
        
        # Get initial file modification times
        def get_file_mtimes(directory: str) -> dict:
            """Get modification times for all files in directory"""
            mtimes = {}
            try:
                for root, dirs, files in os.walk(directory):
                    # Skip node_modules and .expo
                    dirs[:] = [d for d in dirs if d not in ['node_modules', '.expo', '.git']]
                    
                    for file in files:
                        if file.endswith(('.tsx', '.ts', '.jsx', '.js', '.json')):
                            file_path = os.path.join(root, file)
                            try:
                                mtimes[file_path] = os.path.getmtime(file_path)
                            except:
                                pass
            except Exception as e:
                logger.error(f"Error getting file mtimes: {e}")
            return mtimes
        
        last_mtimes = get_file_mtimes(project.directory)
        last_notification_time = 0
        debounce_seconds = 2  # Wait 2 seconds between notifications
        
        # Watch for file changes
        while True:
            try:
                # Check for changes every 1 second
                await asyncio.sleep(1)
                
                current_mtimes = get_file_mtimes(project.directory)
                
                # Find changed files
                changed_files = []
                for file_path, mtime in current_mtimes.items():
                    if file_path not in last_mtimes or last_mtimes[file_path] != mtime:
                        relative_path = os.path.relpath(file_path, project.directory)
                        changed_files.append(relative_path)
                
                # Check for deleted files
                for file_path in last_mtimes:
                    if file_path not in current_mtimes:
                        relative_path = os.path.relpath(file_path, project.directory)
                        changed_files.append(relative_path)
                
                # Send notification if files changed (with debounce)
                current_time = time.time()
                if changed_files and (current_time - last_notification_time) >= debounce_seconds:
                    logger.info(f"Files changed in project {validated_project_id}: {changed_files}")
                    try:
                        await websocket.send_json({
                            "type": "file_change",
                            "files": changed_files,
                            "timestamp": current_time
                        })
                        last_mtimes = current_mtimes
                        last_notification_time = current_time
                    except Exception as send_error:
                        logger.error(f"Failed to send WebSocket message: {send_error}")
                        break
                elif changed_files:
                    # Update mtimes but don't send notification (debounced)
                    last_mtimes = current_mtimes
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for project {validated_project_id}")
                break
            except Exception as e:
                logger.error(f"Error in file watcher: {e}", exc_info=True)
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"WebSocket file watcher closed for project {validated_project_id}")


# File Management Endpoints
from services.file_manager import FileManager

file_manager = FileManager()

class FileContentRequest(BaseModel):
    content: str

class FileCreateRequest(BaseModel):
    path: str
    type: str
    content: str = ""

class FileRenameRequest(BaseModel):
    new_name: str

@app.get("/files/{project_id}/{file_path:path}/content")
async def get_file_content(project_id: str, file_path: str):
    """Get file content"""
    try:
        validated_project_id = validate_project_id(project_id)
        content = file_manager.read_file(validated_project_id, file_path)
        if content is None:
            return JSONResponse(status_code=404, content={"error": "File not found"})
        return {"content": content, "path": file_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/files/{project_id}/{file_path:path}")
async def serve_file(project_id: str, file_path: str):
    """Serve raw file (for images, etc.)"""
    try:
        validated_project_id = validate_project_id(project_id)
        project = project_manager.get_project(validated_project_id)
        if not project:
            return JSONResponse(status_code=404, content={"error": "Project not found"})
        
        full_path = os.path.join(project.directory, file_path)
        
        if not os.path.exists(full_path):
            return JSONResponse(status_code=404, content={"error": "File not found"})
        
        # Determine media type based on extension
        ext = file_path.split('.')[-1].lower()
        media_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'webp': 'image/webp',
            'bmp': 'image/bmp',
            'ico': 'image/x-icon',
        }
        
        media_type = media_types.get(ext, 'application/octet-stream')
        
        # Return file as response
        return FileResponse(full_path, media_type=media_type)
        
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/files/{project_id}/{file_path:path}")
async def update_file(project_id: str, file_path: str, request: FileContentRequest):
    """Update file - automatically generates icons and images if it's a screen file"""
    try:
        validated_project_id = validate_project_id(project_id)
        project = project_manager.get_project(validated_project_id)
        
        if not project:
            return JSONResponse(status_code=404, content={"error": "Project not found"})
        
        success = file_manager.write_file(validated_project_id, file_path, request.content)
        if not success:
            return JSONResponse(status_code=500, content={"error": "Failed to write"})
        
        # If this is a screen file (.tsx), enhance it with icons and generate images
        if file_path.endswith('.tsx') and 'app' in file_path:
            try:
                await enhance_screen_with_icons_and_images(
                    project_id=validated_project_id,
                    file_path=file_path,
                    content=request.content,
                    project_dir=project.directory
                )
            except Exception as e:
                logger.warning(f"Failed to enhance screen with icons/images: {e}")
                # Don't fail the update if enhancement fails
        
        return {"success": True, "path": file_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/files/{project_id}")
async def create_file(project_id: str, request: FileCreateRequest):
    """Create file/folder - automatically generates icons and images if it's a screen file"""
    try:
        validated_project_id = validate_project_id(project_id)
        project = project_manager.get_project(validated_project_id)
        
        if not project:
            return JSONResponse(status_code=404, content={"error": "Project not found"})
        
        if request.type == 'folder':
            success = file_manager.create_folder(validated_project_id, request.path)
        else:
            success = file_manager.create_file(validated_project_id, request.path, request.content)
        
        if not success:
            return JSONResponse(status_code=500, content={"error": "Failed to create"})
        
        # If this is a screen file (.tsx), enhance it with icons and generate images
        if request.type != 'folder' and request.path.endswith('.tsx') and 'app' in request.path:
            try:
                await enhance_screen_with_icons_and_images(
                    project_id=validated_project_id,
                    file_path=request.path,
                    content=request.content,
                    project_dir=project.directory
                )
            except Exception as e:
                logger.warning(f"Failed to enhance screen with icons/images: {e}")
                # Don't fail the creation if enhancement fails
        
        return {"success": True, "path": request.path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/files/{project_id}/{file_path:path}")
async def delete_file(project_id: str, file_path: str):
    """Delete file"""
    try:
        validated_project_id = validate_project_id(project_id)
        success = file_manager.delete_file(validated_project_id, file_path)
        if not success:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/files/{project_id}/{file_path:path}/rename")
async def rename_file(project_id: str, file_path: str, request: FileRenameRequest):
    """Rename file"""
    try:
        validated_project_id = validate_project_id(project_id)
        success = file_manager.rename_file(validated_project_id, file_path, request.new_name)
        if not success:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        return {"success": True, "new_name": request.new_name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Screen/File Generation
class GenerateScreenRequest(BaseModel):
    prompt: str
    project_id: str

@app.post("/generate-screen")
async def generate_screen(request: GenerateScreenRequest, api_key: str = Depends(verify_api_key)):
    """Generate new screen/component files based on prompt"""
    logger.info(f"Screen generation endpoint called with prompt: {request.prompt[:50]}...")
    
    try:
        validated_project_id = validate_project_id(request.project_id)
        sanitized_prompt = sanitize_prompt(request.prompt)
        
        logger.info(f"Screen generation request for project {validated_project_id}: {sanitized_prompt[:100]}...")
        
        project = project_manager.get_project(validated_project_id)
        if not project:
            raise ProjectNotFoundError(validated_project_id)
        
        # Build AI prompt for screen generation
        screen_prompt = f"""You are an expert React Native developer. Generate new screen/component files based on the user's request.

User Request:
{sanitized_prompt}

Instructions:
1. Determine what files need to be created (screens, components, utilities, etc.)
2. Generate complete, production-ready code for each file
3. Use React Native and Expo best practices
4. Include proper TypeScript types
5. Add necessary imports
6. Follow the project structure (app/ for screens, components/ for reusable components)
7. Make screens responsive and accessible

Output Format:
For each file to create, output:
// CREATE: <filepath>
<complete file content>
// END_CREATE

Example:
// CREATE: app/profile.tsx
import {{ View, Text }} from 'react-native';
export default function ProfileScreen() {{
  return <View><Text>Profile</Text></View>;
}}
// END_CREATE

Provide a brief summary at the end starting with "SUMMARY:"
"""
        
        # Call AI
        try:
            logger.info("Calling AI to generate screen code...")
            response = await asyncio.wait_for(
                code_generator.client.responses.create(
                    model=code_generator.model,
                    input=screen_prompt
                ),
                timeout=60.0
            )
            
            ai_response = response.output_text
            logger.info(f"AI response received, length: {len(ai_response)}")
        except asyncio.TimeoutError:
            logger.error("AI generation timed out")
            raise TimeoutError("Screen generation timed out after 60 seconds")
        except Exception as ai_error:
            logger.error(f"AI generation failed: {ai_error}", exc_info=True)
            raise
        
        # Parse AI response to extract files
        file_pattern = r'// CREATE: (.+?)\n(.*?)// END_CREATE'
        matches = re.findall(file_pattern, ai_response, re.DOTALL)
        
        logger.info(f"Found {len(matches)} files to create")
        
        if not matches:
            logger.warning("No files found in AI response")
            logger.debug(f"AI response: {ai_response[:500]}...")
        
        created_files = []
        for file_path, content in matches:
            file_path = file_path.strip()
            content = content.strip()
            
            # Create the file
            full_path = os.path.join(project.directory, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(file_path)
            logger.info(f"Created file: {file_path}")
        
        # Extract summary
        summary_match = re.search(r'SUMMARY:\s*(.+?)(?:\n\n|$)', ai_response, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else "Files created successfully"
        
        # Trigger Metro reload
        file_manager._trigger_reload(validated_project_id)
        
        return {
            "success": True,
            "files_created": created_files,
            "summary": summary,
            "message": f"Created {len(created_files)} file(s)"
        }
        
    except SanitizationError as e:
        logger.warning(f"Screen generation sanitization error: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid input: {str(e)}"}
        )
    except ProjectNotFoundError as e:
        logger.warning(f"Project not found: {e}")
        return JSONResponse(
            status_code=404,
            content={"error": str(e)}
        )
    except TimeoutError as e:
        logger.error(f"Screen generation timeout: {e}")
        return JSONResponse(
            status_code=504,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error generating screen: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Screen generation failed: {str(e)}"}
        )


# Image Generation
import uuid
from datetime import datetime

class ImageGenerateRequest(BaseModel):
    prompt: str
    project_id: str

@app.post("/generate-image")
async def generate_image(request: ImageGenerateRequest):
    """Generate image using AI with Gemini/OpenAI fallback"""
    try:
        logger.info(f"Image generation request: {request.prompt[:50]}...")
        
        # Validate inputs
        validated_project_id = validate_project_id(request.project_id)
        sanitized_prompt = sanitize_prompt(request.prompt)
        
        # Check if project exists
        project = project_manager.get_project(validated_project_id)
        if not project:
            logger.warning(f"Image generation for non-existent project: {validated_project_id}")
            return JSONResponse(
                status_code=404,
                content={"error": "Project not found"}
            )
        
        # Create assets directory
        project_path = os.path.join("projects", validated_project_id)
        assets_path = os.path.join(project_path, "assets", "images")
        os.makedirs(assets_path, exist_ok=True)
        
        # Generate filename
        filename = f"generated_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(assets_path, filename)
        
        # Try to generate image with AI
        try:
            logger.info("Importing AIImageGenerator...")
            from services.gemini_image import AIImageGenerator
            
            logger.info("Initializing image generator...")
            image_generator = AIImageGenerator()
            
            logger.info(f"Generating image with prompt: {sanitized_prompt[:50]}...")
            # Generate image (tries Gemini first, falls back to OpenAI)
            image_data, provider = image_generator.generate_image(sanitized_prompt)
            
            logger.info(f"Generation result - Image data: {image_data is not None}, Provider: {provider}")
            
            if image_data:
                # Save the generated image
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"Image generated successfully with {provider}: {filename}")
                
                return {
                    "success": True,
                    "filename": filename,
                    "path": f"assets/images/{filename}",
                    "image_url": f"/projects/{validated_project_id}/assets/images/{filename}",
                    "message": f"Image generated successfully with {provider.upper()}",
                    "provider": provider,
                    "is_placeholder": False
                }
            else:
                # No providers available or all failed - provider contains error message
                error_msg = f"Image generation failed: {provider}"
                logger.warning(error_msg)
                raise ValueError(error_msg)
                
        except Exception as gen_error:
            logger.warning(f"AI image generation failed: {gen_error}")
            
            # Create placeholder text file
            placeholder_content = f"""Image Generation Placeholder

Prompt: {sanitized_prompt}
Generated: {datetime.now().isoformat()}
Filename: {filename}

Error: {str(gen_error)}

To enable real image generation:
1. Add GEMINI_API_KEY to backend/.env (for Gemini)
2. OpenAI key already configured (DALL-E fallback)
3. Install: pip install openai google-generativeai
4. See GEMINI_SETUP.md for details
"""
            
            # Save placeholder
            placeholder_path = file_path.replace('.png', '.txt')
            with open(placeholder_path, 'w', encoding='utf-8') as f:
                f.write(placeholder_content)
            
            logger.info(f"Image placeholder created: {filename}")
            
            return {
                "success": True,
                "filename": filename.replace('.png', '.txt'),
                "path": f"assets/images/{filename.replace('.png', '.txt')}",
                "image_url": f"/projects/{validated_project_id}/assets/images/{filename}",
                "message": f"Image generation not available: {str(gen_error)}. Placeholder created.",
                "is_placeholder": True,
                "error": str(gen_error)
            }
        
    except SanitizationError as e:
        logger.warning(f"Image generation sanitization error: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid input: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Image generation error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate image: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
