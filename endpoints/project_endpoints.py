"""
Project Management Endpoints
Simple endpoints for checking project status
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


class ProjectStatusResponse(BaseModel):
    """Simple project status response"""
    project_id: str
    status: str
    preview_url: Optional[str] = None
    error: Optional[str] = None
    exists: bool


@router.get("/project-status/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status_simple(project_id: str):
    """
    Simple project status check
    
    Returns basic status information without requiring full project details.
    Useful for polling during generation.
    """
    from main import project_manager
    
    # Check if project exists
    project = project_manager.get_project(project_id)
    
    if not project:
        # Project doesn't exist yet or was cleaned up
        return ProjectStatusResponse(
            project_id=project_id,
            status="not_found",
            preview_url=None,
            error=None,
            exists=False
        )
    
    # Return project status
    return ProjectStatusResponse(
        project_id=project.id,
        status=project.status.value,
        preview_url=project.preview_url,
        error=project.error_message,
        exists=True
    )


@router.get("/quick-status/{project_id}")
async def get_quick_status(project_id: str):
    """
    Ultra-fast status check
    
    Returns minimal information for quick polling.
    """
    from main import project_manager
    
    project = project_manager.get_project(project_id)
    
    if not project:
        return {
            "exists": False,
            "status": "not_found"
        }
    
    return {
        "exists": True,
        "status": project.status.value,
        "ready": project.status.value == "ready",
        "url": project.preview_url,
        "error": project.error_message
    }


@router.get("/download-from-storage/{project_id}")
async def download_from_storage(project_id: str):
    """
    Download project from Cloud Storage
    
    Retrieves project ZIP from GCS bucket.
    """
    from main import cloud_storage_manager
    from fastapi.responses import StreamingResponse
    import io
    
    try:
        # Get blob from GCS
        blob_name = f"projects/{project_id}.zip"
        blob = cloud_storage_manager.bucket.blob(blob_name)
        
        if not blob.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found in Cloud Storage"
            )
        
        # Download to memory
        zip_data = blob.download_as_bytes()
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_data),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=project-{project_id[:8]}.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download from storage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download project: {str(e)}"
        )
