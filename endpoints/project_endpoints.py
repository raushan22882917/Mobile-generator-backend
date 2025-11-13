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
    
    if not cloud_storage_manager or not cloud_storage_manager.is_available():
        raise HTTPException(
            status_code=503,
            detail="Cloud Storage not configured. Cannot download projects."
        )
    
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


class BucketProjectInfo(BaseModel):
    """Information about a project in Cloud Storage"""
    project_id: str
    file_name: str
    size_mb: float
    created_at: str
    updated_at: str
    gcs_path: str
    download_url: str


class BucketProjectsResponse(BaseModel):
    """Response for listing bucket projects"""
    total_projects: int
    total_size_mb: float
    projects: list[BucketProjectInfo]
    bucket_name: str


@router.get("/bucket-projects", response_model=BucketProjectsResponse)
async def list_bucket_projects():
    """
    List all projects stored in Cloud Storage bucket
    
    Returns detailed information about each project including:
    - Project ID
    - File size
    - Creation/update timestamps
    - Download URLs
    """
    from main import cloud_storage_manager
    from config import settings
    
    if not cloud_storage_manager or not cloud_storage_manager.is_available():
        raise HTTPException(
            status_code=503,
            detail="Cloud Storage not configured. Cannot list projects."
        )
    
    try:
        # List all blobs in the projects/ folder
        blobs = list(cloud_storage_manager.bucket.list_blobs(prefix="projects/"))
        
        projects = []
        total_size = 0
        
        for blob in blobs:
            project_id = blob.name.replace("projects/", "").replace(".zip", "")
            size_mb = blob.size / (1024 * 1024)  # Convert to MB
            total_size += size_mb
            
            projects.append(BucketProjectInfo(
                project_id=project_id,
                file_name=blob.name,
                size_mb=round(size_mb, 2),
                created_at=blob.time_created.isoformat(),
                updated_at=blob.updated.isoformat(),
                gcs_path=f"gs://{settings.google_cloud_bucket}/{blob.name}",
                download_url=f"/download-from-storage/{project_id}"
            ))
        
        logger.info(f"Listed {len(projects)} projects from Cloud Storage")
        
        return BucketProjectsResponse(
            total_projects=len(projects),
            total_size_mb=round(total_size, 2),
            projects=projects,
            bucket_name=settings.google_cloud_bucket
        )
        
    except Exception as e:
        logger.error(f"Failed to list bucket projects: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list projects: {str(e)}"
        )
