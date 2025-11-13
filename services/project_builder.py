"""
Project Builder Service
Handles dynamic building and preview of projects on demand
"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectBuilder:
    """
    Manages dynamic project building and preview
    
    Features:
    - Build projects on demand (not during generation)
    - Hot reload support
    - Efficient resource usage
    """
    
    def __init__(self, shared_deps_manager):
        """
        Initialize project builder
        
        Args:
            shared_deps_manager: SharedDependenciesManager instance
        """
        self.shared_deps_manager = shared_deps_manager
        self.active_builds: Dict[str, asyncio.subprocess.Process] = {}
        
        logger.info("Project builder initialized")
    
    async def build_project(
        self,
        project_id: str,
        project_dir: str,
        port: int,
        use_shared_deps: bool = True
    ) -> asyncio.subprocess.Process:
        """
        Build and start project server
        
        Args:
            project_id: Project identifier
            project_dir: Project directory path
            port: Port to run server on
            use_shared_deps: Whether to use shared dependencies
            
        Returns:
            Server process
        """
        logger.info(f"Building project {project_id} on port {port}")
        
        # Setup dependencies
        if use_shared_deps:
            logger.info("Using shared dependencies")
            await self.shared_deps_manager.setup_project_with_shared_deps(project_dir)
        else:
            logger.info("Installing project-specific dependencies")
            await self._install_local_deps(project_dir)
        
        # Start Expo server
        process = await self._start_server(project_dir, port)
        
        # Track active build
        self.active_builds[project_id] = process
        
        logger.info(f"Project {project_id} built and running (PID: {process.pid})")
        return process
    
    async def _install_local_deps(self, project_dir: str):
        """Install dependencies locally in project"""
        logger.info(f"Installing dependencies in {project_dir}")
        
        process = await asyncio.create_subprocess_exec(
            "npm", "install", "--legacy-peer-deps",
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"npm install failed: {error_msg}")
            raise Exception(f"Failed to install dependencies: {error_msg}")
        
        logger.info("Dependencies installed successfully")
    
    async def _start_server(self, project_dir: str, port: int) -> asyncio.subprocess.Process:
        """Start Expo development server"""
        logger.info(f"Starting Expo server on port {port}")
        
        # Set environment variables
        env = os.environ.copy()
        env['PORT'] = str(port)
        env['EXPO_DEVTOOLS_LISTEN_ADDRESS'] = '0.0.0.0'
        
        # Start server
        process = await asyncio.create_subprocess_exec(
            "npx", "expo", "start", "--port", str(port), "--non-interactive",
            cwd=project_dir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for server to be ready
        await asyncio.sleep(5)
        
        if process.returncode is not None:
            raise Exception("Expo server failed to start")
        
        logger.info(f"Expo server started (PID: {process.pid})")
        return process
    
    async def stop_build(self, project_id: str):
        """
        Stop a running build
        
        Args:
            project_id: Project identifier
        """
        if project_id not in self.active_builds:
            logger.warning(f"No active build for project {project_id}")
            return
        
        process = self.active_builds[project_id]
        
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=10)
            logger.info(f"Build stopped for project {project_id}")
        except asyncio.TimeoutError:
            logger.warning(f"Build did not stop gracefully, killing process")
            process.kill()
            await process.wait()
        finally:
            del self.active_builds[project_id]
    
    async def rebuild_project(self, project_id: str, project_dir: str, port: int):
        """
        Rebuild a project (stop and restart)
        
        Args:
            project_id: Project identifier
            project_dir: Project directory
            port: Port to run on
        """
        logger.info(f"Rebuilding project {project_id}")
        
        # Stop existing build
        await self.stop_build(project_id)
        
        # Start new build
        return await self.build_project(project_id, project_dir, port)
    
    def is_building(self, project_id: str) -> bool:
        """Check if project is currently building"""
        return project_id in self.active_builds
    
    def get_active_builds(self) -> list:
        """Get list of active build project IDs"""
        return list(self.active_builds.keys())
    
    async def cleanup_all(self):
        """Stop all active builds"""
        logger.info("Stopping all active builds")
        
        for project_id in list(self.active_builds.keys()):
            await self.stop_build(project_id)
        
        logger.info("All builds stopped")
