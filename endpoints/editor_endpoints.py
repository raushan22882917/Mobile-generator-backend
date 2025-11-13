"""
Web Editor Endpoints
Provides API for web-based code editor (like Lovable.dev)
"""
import os
import logging
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/editor", tags=["editor"])


class FileContent(BaseModel):
    """File content model"""
    path: str
    content: str
    language: Optional[str] = None


class FileUpdate(BaseModel):
    """File update model"""
    path: str
    content: str


class FileTree(BaseModel):
    """File tree node model"""
    name: str
    path: str
    type: str  # "file" or "folder"
    children: Optional[List['FileTree']] = None
    size: Optional[int] = None


class ProjectInfo(BaseModel):
    """Project information model"""
    project_id: str
    name: str
    status: str
    preview_url: Optional[str] = None
    file_count: int
    total_size: int


@router.get("/projects/{project_id}/files")
async def get_project_files(project_id: str):
    """
    Get file tree for project
    
    Returns hierarchical file structure for web editor
    """
    from main import project_manager, cloud_storage_manager
    
    # Try to get project from memory
    project = project_manager.get_project(project_id)
    
    if not project:
        # Try to download from cloud storage
        if cloud_storage_manager and cloud_storage_manager.is_available():
            logger.info(f"Downloading project {project_id} from cloud storage")
            project_dir = Path(f"/tmp/projects/{project_id}")
            project_dir.mkdir(parents=True, exist_ok=True)
            
            success = await cloud_storage_manager.download_project(
                project_id,
                str(project_dir)
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="Project not found")
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        project_dir = Path(project.directory)
    
    # Build file tree
    def build_tree(path: Path, base_path: Path) -> FileTree:
        """Recursively build file tree"""
        relative_path = str(path.relative_to(base_path))
        
        if path.is_file():
            return FileTree(
                name=path.name,
                path=relative_path,
                type="file",
                size=path.stat().st_size
            )
        
        # Directory
        children = []
        try:
            for item in sorted(path.iterdir()):
                # Skip node_modules and build artifacts
                if item.name in ['node_modules', '.expo', '.git', 'dist', 'build']:
                    continue
                
                children.append(build_tree(item, base_path))
        except PermissionError:
            pass
        
        return FileTree(
            name=path.name,
            path=relative_path,
            type="folder",
            children=children
        )
    
    file_tree = build_tree(project_dir, project_dir)
    
    return {
        "project_id": project_id,
        "file_tree": file_tree
    }


@router.get("/projects/{project_id}/file")
async def get_file_content(project_id: str, path: str):
    """
    Get content of a specific file
    
    Args:
        project_id: Project identifier
        path: Relative file path
    """
    from main import project_manager, cloud_storage_manager
    
    # Get project directory
    project = project_manager.get_project(project_id)
    
    if not project:
        # Try cloud storage
        if cloud_storage_manager and cloud_storage_manager.is_available():
            project_dir = Path(f"/tmp/projects/{project_id}")
            if not project_dir.exists():
                project_dir.mkdir(parents=True, exist_ok=True)
                await cloud_storage_manager.download_project(project_id, str(project_dir))
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        project_dir = Path(project.directory)
    
    # Read file
    file_path = project_dir / path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Security check - ensure file is within project directory
    try:
        file_path.resolve().relative_to(project_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Read content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Detect language from extension
        ext = file_path.suffix.lower()
        language_map = {
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.json': 'json',
            '.css': 'css',
            '.html': 'html',
            '.md': 'markdown',
            '.py': 'python'
        }
        language = language_map.get(ext, 'plaintext')
        
        return FileContent(
            path=path,
            content=content,
            language=language
        )
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/projects/{project_id}/file")
async def update_file_content(project_id: str, file_update: FileUpdate):
    """
    Update file content
    
    Args:
        project_id: Project identifier
        file_update: File update data
    """
    from main import project_manager, cloud_storage_manager
    
    # Get project directory
    project = project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = Path(project.directory)
    file_path = project_dir / file_update.path
    
    # Security check
    try:
        file_path.resolve().relative_to(project_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create parent directories if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_update.content)
        
        logger.info(f"Updated file: {file_update.path}")
        
        # Upload to cloud storage if available
        if cloud_storage_manager and cloud_storage_manager.is_available():
            await cloud_storage_manager.upload_project(project_id, str(project_dir))
        
        return {"success": True, "message": "File updated successfully"}
    except Exception as e:
        logger.error(f"Error updating file {file_update.path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")


@router.delete("/projects/{project_id}/file")
async def delete_file(project_id: str, path: str):
    """
    Delete a file
    
    Args:
        project_id: Project identifier
        path: Relative file path
    """
    from main import project_manager
    
    project = project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = Path(project.directory)
    file_path = project_dir / path
    
    # Security check
    try:
        file_path.resolve().relative_to(project_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file
    try:
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
        
        logger.info(f"Deleted: {path}")
        return {"success": True, "message": "File deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@router.post("/projects/{project_id}/create-file")
async def create_file(project_id: str, file_update: FileUpdate):
    """
    Create a new file
    
    Args:
        project_id: Project identifier
        file_update: File data
    """
    return await update_file_content(project_id, file_update)


@router.post("/projects/{project_id}/preview")
async def start_preview(project_id: str):
    """
    Start preview server for project
    
    Builds project and creates preview URL
    """
    from main import project_manager, project_builder, tunnel_manager
    
    project = project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if already running
    if project_builder.is_building(project_id):
        return {
            "success": True,
            "message": "Preview already running",
            "preview_url": project.preview_url
        }
    
    try:
        # Build project
        await project_builder.build_project(
            project_id,
            project.directory,
            project.port
        )
        
        # Create tunnel if not exists
        if not project.preview_url:
            preview_url = await tunnel_manager.create_tunnel(
                project.port,
                project_id
            )
            project_manager.update_preview_url(project_id, preview_url)
        
        return {
            "success": True,
            "message": "Preview started",
            "preview_url": project.preview_url
        }
    except Exception as e:
        logger.error(f"Failed to start preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start preview: {str(e)}")


@router.post("/projects/{project_id}/stop-preview")
async def stop_preview(project_id: str):
    """
    Stop preview server
    
    Args:
        project_id: Project identifier
    """
    from main import project_builder
    
    try:
        await project_builder.stop_build(project_id)
        return {"success": True, "message": "Preview stopped"}
    except Exception as e:
        logger.error(f"Failed to stop preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop preview: {str(e)}")


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time updates
    
    Provides:
    - File change notifications
    - Build status updates
    - Console output
    """
    await websocket.accept()
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for now (can be extended for real-time features)
            await websocket.send_json({
                "type": "pong",
                "timestamp": str(datetime.now())
            })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for project {project_id}")
