"""
Build Endpoints
Handles dynamic project building with shared dependencies
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/build", tags=["build"])


class BuildRequest(BaseModel):
    """Build request model"""
    use_shared_deps: bool = True
    force_rebuild: bool = False


class BuildResponse(BaseModel):
    """Build response model"""
    project_id: str
    status: str
    preview_url: Optional[str] = None
    message: str
    using_shared_deps: bool


class BuildStatusResponse(BaseModel):
    """Build status response"""
    project_id: str
    is_building: bool
    is_running: bool
    preview_url: Optional[str] = None


@router.post("/projects/{project_id}/build", response_model=BuildResponse)
async def build_project(project_id: str, build_request: BuildRequest):
    """
    Build project with shared dependencies
    
    This endpoint:
    1. Downloads project from Cloud Storage if needed
    2. Uses shared node_modules to avoid redundant installations
    3. Starts preview server
    4. Creates tunnel for remote access
    
    Args:
        project_id: Project identifier
        build_request: Build configuration
    """
    from main import (
        project_manager,
        cloud_storage_manager,
        project_builder,
        tunnel_manager
    )
    
    logger.info(f"Build requested for project {project_id}")
    
    # Check if project exists in memory
    project = project_manager.get_project(project_id)
    
    # If not in memory, try to download from cloud storage
    if not project:
        if not cloud_storage_manager or not cloud_storage_manager.is_available():
            raise HTTPException(
                status_code=404,
                detail="Project not found and Cloud Storage not available"
            )
        
        logger.info(f"Downloading project {project_id} from Cloud Storage")
        
        import os
        from pathlib import Path
        from datetime import datetime
        import models.project
        
        # Create project directory
        project_dir = os.path.join(
            project_manager.base_dir,
            project_id
        )
        os.makedirs(project_dir, exist_ok=True)
        
        # Download from cloud storage
        success = await cloud_storage_manager.download_project(
            project_id,
            project_dir
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Project not found in Cloud Storage"
            )
        
        # Create project object
        port = project_manager.port_manager.allocate_port()
        project = models.project.Project(
            id=project_id,
            user_id="unknown",
            prompt="",
            directory=project_dir,
            port=port,
            status=models.project.ProjectStatus.READY,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        project_manager.active_projects[project_id] = project
        logger.info(f"Project {project_id} restored from Cloud Storage")
    
    # Check if already building
    if project_builder.is_building(project_id) and not build_request.force_rebuild:
        return BuildResponse(
            project_id=project_id,
            status="already_building",
            preview_url=project.preview_url,
            message="Project is already building",
            using_shared_deps=build_request.use_shared_deps
        )
    
    try:
        # Stop existing build if force rebuild
        if build_request.force_rebuild and project_builder.is_building(project_id):
            logger.info(f"Force rebuilding project {project_id}")
            await project_builder.stop_build(project_id)
        
        # Build project
        logger.info(f"Building project {project_id} (shared_deps={build_request.use_shared_deps})")
        await project_builder.build_project(
            project_id,
            project.directory,
            project.port,
            use_shared_deps=build_request.use_shared_deps
        )
        
        # Create tunnel if not exists
        if not project.preview_url:
            logger.info(f"Creating tunnel for project {project_id}")
            preview_url = await tunnel_manager.create_tunnel(
                project.port,
                project_id
            )
            project_manager.update_preview_url(project_id, preview_url)
        
        return BuildResponse(
            project_id=project_id,
            status="success",
            preview_url=project.preview_url,
            message="Project built successfully",
            using_shared_deps=build_request.use_shared_deps
        )
        
    except Exception as e:
        logger.error(f"Failed to build project {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Build failed: {str(e)}"
        )


@router.get("/projects/{project_id}/build-status", response_model=BuildStatusResponse)
async def get_build_status(project_id: str):
    """
    Get build status for project
    
    Args:
        project_id: Project identifier
    """
    from main import project_manager, project_builder
    
    project = project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    is_building = project_builder.is_building(project_id)
    
    return BuildStatusResponse(
        project_id=project_id,
        is_building=is_building,
        is_running=is_building,
        preview_url=project.preview_url
    )


@router.post("/projects/{project_id}/stop")
async def stop_build(project_id: str):
    """
    Stop project build/server
    
    Args:
        project_id: Project identifier
    """
    from main import project_builder
    
    try:
        await project_builder.stop_build(project_id)
        return {
            "success": True,
            "message": "Build stopped successfully"
        }
    except Exception as e:
        logger.error(f"Failed to stop build: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop build: {str(e)}"
        )


@router.post("/projects/{project_id}/rebuild")
async def rebuild_project(project_id: str):
    """
    Rebuild project (stop and restart)
    
    Args:
        project_id: Project identifier
    """
    from main import project_manager, project_builder
    
    project = project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        logger.info(f"Rebuilding project {project_id}")
        await project_builder.rebuild_project(
            project_id,
            project.directory,
            project.port
        )
        
        return {
            "success": True,
            "message": "Project rebuilt successfully",
            "preview_url": project.preview_url
        }
    except Exception as e:
        logger.error(f"Failed to rebuild project: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Rebuild failed: {str(e)}"
        )


@router.get("/active-builds")
async def list_active_builds():
    """
    List all active builds
    
    Returns list of project IDs with active builds
    """
    from main import project_builder
    
    active_builds = project_builder.get_active_builds()
    
    return {
        "active_builds": active_builds,
        "count": len(active_builds)
    }


@router.post("/cleanup-shared-deps")
async def cleanup_shared_dependencies(max_age_days: int = 7):
    """
    Clean up old shared dependency caches
    
    Args:
        max_age_days: Maximum age in days (default: 7)
    """
    from main import shared_deps_manager
    
    try:
        shared_deps_manager.cleanup_old_caches(max_age_days)
        return {
            "success": True,
            "message": f"Cleaned up caches older than {max_age_days} days"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup caches: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )
