"""
Streaming Generation Endpoint
Real-time app generation with WebSocket updates
"""
import asyncio
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.websocket_manager import connection_manager
from services.streaming_generator import StreamingGenerator, ProgressUpdate
from middleware.auth import verify_api_key
from utils.sanitization import sanitize_prompt, sanitize_user_id, SanitizationError
from exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamingGenerateRequest(BaseModel):
    """Request model for streaming generation"""
    prompt: str = Field(..., min_length=10, max_length=5000)
    user_id: Optional[str] = Field(default="anonymous")
    template_id: Optional[str] = Field(default=None)
    fast_mode: Optional[bool] = Field(default=False, description="Skip additional screens for faster preview")


class StreamingGenerateResponse(BaseModel):
    """Response model for streaming generation"""
    project_id: str
    websocket_url: str
    message: str


async def create_streaming_generator():
    """Dependency to get streaming generator instance"""
    # Import here to avoid circular imports
    from main import (
        code_generator,
        screen_generator,
        project_manager,
        command_executor,
        tunnel_manager,
        cloud_storage_manager
    )
    
    if not all([code_generator, screen_generator, project_manager, 
                command_executor, tunnel_manager]):
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    return StreamingGenerator(
        code_generator=code_generator,
        screen_generator=screen_generator,
        project_manager=project_manager,
        command_executor=command_executor,
        tunnel_manager=tunnel_manager,
        cloud_storage_manager=cloud_storage_manager
    )


@router.post("/generate-stream", response_model=StreamingGenerateResponse)
async def initiate_streaming_generation(
    request: StreamingGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Initiate streaming app generation
    
    Returns a project_id and WebSocket URL for real-time updates.
    Client should connect to WebSocket to receive progress updates.
    """
    try:
        # Sanitize inputs
        sanitized_prompt = sanitize_prompt(request.prompt)
        sanitized_user_id = sanitize_user_id(request.user_id)
    except SanitizationError as e:
        logger.warning(f"Input sanitization failed: {str(e)}")
        raise ValidationError(str(e))
    
    # Generate unique project ID
    project_id = str(uuid.uuid4())
    
    logger.info(f"Initiated streaming generation for project {project_id}")
    
    # Return immediately with WebSocket URL
    return StreamingGenerateResponse(
        project_id=project_id,
        websocket_url=f"/ws/generate/{project_id}",
        message="Connect to WebSocket for real-time updates"
    )


@router.websocket("/ws/generate/{project_id}")
async def websocket_generate_endpoint(
    websocket: WebSocket,
    project_id: str
):
    """
    WebSocket endpoint for real-time app generation
    
    Client connects here after calling /generate-stream.
    Receives real-time progress updates as app is generated.
    """
    await connection_manager.connect(websocket, project_id)
    
    try:
        # Wait for start signal from client
        data = await websocket.receive_json()
        
        if data.get("action") != "start":
            await websocket.send_json({
                "error": "Expected 'start' action"
            })
            return
        
        prompt = data.get("prompt")
        user_id = data.get("user_id", "anonymous")
        template_id = data.get("template_id")
        fast_mode = data.get("fast_mode", False)
        
        if not prompt:
            await websocket.send_json({
                "error": "Missing prompt"
            })
            return
        
        # Sanitize inputs
        try:
            sanitized_prompt = sanitize_prompt(prompt)
            sanitized_user_id = sanitize_user_id(user_id)
        except SanitizationError as e:
            await websocket.send_json({
                "error": f"Invalid input: {str(e)}"
            })
            return
        
        # Create streaming generator
        generator = await create_streaming_generator()
        
        # Define progress callback
        async def send_progress(update: ProgressUpdate):
            """Send progress update to client"""
            await connection_manager.send_to_project(
                project_id,
                {
                    "type": "progress",
                    "data": update.to_dict()
                }
            )
        
        # Start generation
        logger.info(f"Starting streaming generation for project {project_id}")
        
        result = await generator.generate_with_streaming(
            prompt=sanitized_prompt,
            user_id=sanitized_user_id,
            project_id=project_id,
            progress_callback=send_progress,
            skip_screens=fast_mode
        )
        
        # Send final result
        await connection_manager.send_to_project(
            project_id,
            {
                "type": "complete",
                "data": result
            }
        )
        
        logger.info(f"Streaming generation complete for project {project_id}")
        
        # Keep connection open for a bit
        await asyncio.sleep(2)
        
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from project {project_id}")
    except Exception as e:
        logger.error(f"Error in streaming generation: {e}", exc_info=True)
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
        except:
            pass
    finally:
        await connection_manager.disconnect(websocket, project_id)


@router.get("/stream-status/{project_id}")
async def get_stream_status(project_id: str):
    """Get current status of a streaming generation"""
    connection_count = connection_manager.get_connection_count(project_id)
    
    return {
        "project_id": project_id,
        "active_connections": connection_count,
        "status": "active" if connection_count > 0 else "inactive"
    }
