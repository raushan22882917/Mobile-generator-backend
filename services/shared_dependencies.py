"""
Shared Dependencies Manager
Manages a global node_modules directory to avoid redundant installations
"""
import os
import logging
import asyncio
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class SharedDependenciesManager:
    """
    Manages shared node_modules directory for all projects
    
    Benefits:
    - Reduces disk space usage
    - Faster project setup (no repeated npm installs)
    - Consistent dependency versions across projects
    """
    
    def __init__(self, shared_dir: str = "/tmp/shared_node_modules"):
        """
        Initialize shared dependencies manager
        
        Args:
            shared_dir: Directory for shared node_modules
        """
        self.shared_dir = Path(shared_dir)
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache directory for different dependency sets
        self.cache_dir = self.shared_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Lock file for concurrent access
        self.lock_file = self.shared_dir / ".lock"
        
        logger.info(f"Shared dependencies manager initialized: {self.shared_dir}")
    
    def get_dependency_hash(self, dependencies: Dict[str, str]) -> str:
        """
        Generate hash for a set of dependencies
        
        Args:
            dependencies: Dict of package names to versions
            
        Returns:
            Hash string
        """
        # Sort dependencies for consistent hashing
        sorted_deps = json.dumps(dependencies, sort_keys=True)
        return hashlib.md5(sorted_deps.encode()).hexdigest()[:12]
    
    async def get_or_create_shared_modules(
        self,
        dependencies: Dict[str, str],
        dev_dependencies: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Get or create shared node_modules for given dependencies
        
        Args:
            dependencies: Production dependencies
            dev_dependencies: Development dependencies
            
        Returns:
            Path to shared node_modules directory
        """
        # Combine all dependencies
        all_deps = {**dependencies}
        if dev_dependencies:
            all_deps.update(dev_dependencies)
        
        # Generate hash for this dependency set
        dep_hash = self.get_dependency_hash(all_deps)
        cache_path = self.cache_dir / dep_hash
        node_modules_path = cache_path / "node_modules"
        
        # Check if already cached
        if node_modules_path.exists():
            logger.info(f"Using cached dependencies: {dep_hash}")
            return str(node_modules_path)
        
        # Create new cache entry
        logger.info(f"Creating new dependency cache: {dep_hash}")
        cache_path.mkdir(exist_ok=True)
        
        # Create temporary package.json
        package_json = {
            "name": f"shared-deps-{dep_hash}",
            "version": "1.0.0",
            "dependencies": dependencies,
            "devDependencies": dev_dependencies or {}
        }
        
        package_json_path = cache_path / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Install dependencies
        try:
            process = await asyncio.create_subprocess_exec(
                "npm", "install", "--legacy-peer-deps",
                cwd=str(cache_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Failed to install shared dependencies: {error_msg}")
                raise Exception(f"npm install failed: {error_msg}")
            
            logger.info(f"Shared dependencies installed: {dep_hash}")
            return str(node_modules_path)
            
        except Exception as e:
            logger.error(f"Error installing shared dependencies: {e}")
            # Clean up failed cache
            import shutil
            shutil.rmtree(cache_path, ignore_errors=True)
            raise
    
    async def link_to_project(self, shared_modules_path: str, project_dir: str):
        """
        Link shared node_modules to project directory
        
        Args:
            shared_modules_path: Path to shared node_modules
            project_dir: Project directory
        """
        project_path = Path(project_dir)
        node_modules_link = project_path / "node_modules"
        
        # Remove existing node_modules if present
        if node_modules_link.exists():
            if node_modules_link.is_symlink():
                node_modules_link.unlink()
            else:
                import shutil
                shutil.rmtree(node_modules_link, ignore_errors=True)
        
        # Create symlink to shared modules
        try:
            # On Windows, use junction instead of symlink
            if os.name == 'nt':
                import subprocess
                subprocess.run(
                    ['mklink', '/J', str(node_modules_link), shared_modules_path],
                    shell=True,
                    check=True
                )
            else:
                os.symlink(shared_modules_path, node_modules_link)
            
            logger.info(f"Linked shared modules to {project_dir}")
        except Exception as e:
            logger.error(f"Failed to link shared modules: {e}")
            raise
    
    def get_expo_default_dependencies(self) -> Dict[str, str]:
        """
        Get default Expo dependencies
        
        Returns:
            Dict of default dependencies
        """
        return {
            "expo": "~51.0.0",
            "expo-status-bar": "~1.12.1",
            "react": "18.2.0",
            "react-native": "0.74.5",
            "@expo/vector-icons": "^14.0.0",
            "expo-router": "~3.5.0",
            "expo-linking": "~6.3.0",
            "expo-constants": "~16.0.0",
            "expo-splash-screen": "~0.27.0",
            "expo-font": "~12.0.0"
        }
    
    def get_expo_default_dev_dependencies(self) -> Dict[str, str]:
        """
        Get default Expo dev dependencies
        
        Returns:
            Dict of default dev dependencies
        """
        return {
            "@babel/core": "^7.20.0",
            "@types/react": "~18.2.45",
            "typescript": "^5.1.3"
        }
    
    async def setup_project_with_shared_deps(self, project_dir: str) -> str:
        """
        Setup project with shared dependencies
        
        Args:
            project_dir: Project directory
            
        Returns:
            Path to shared node_modules
        """
        # Read project's package.json
        package_json_path = Path(project_dir) / "package.json"
        
        if not package_json_path.exists():
            # Use default Expo dependencies
            dependencies = self.get_expo_default_dependencies()
            dev_dependencies = self.get_expo_default_dev_dependencies()
        else:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})
        
        # Get or create shared modules
        shared_modules_path = await self.get_or_create_shared_modules(
            dependencies,
            dev_dependencies
        )
        
        # Link to project
        await self.link_to_project(shared_modules_path, project_dir)
        
        return shared_modules_path
    
    def cleanup_old_caches(self, max_age_days: int = 7):
        """
        Clean up old dependency caches
        
        Args:
            max_age_days: Maximum age in days
        """
        logger.info(f"Cleaning up caches older than {max_age_days} days")
        
        cutoff_time = datetime.now().timestamp() - (max_age_days * 86400)
        removed_count = 0
        
        for cache_entry in self.cache_dir.iterdir():
            if not cache_entry.is_dir():
                continue
            
            # Check modification time
            mtime = cache_entry.stat().st_mtime
            if mtime < cutoff_time:
                import shutil
                shutil.rmtree(cache_entry, ignore_errors=True)
                removed_count += 1
                logger.info(f"Removed old cache: {cache_entry.name}")
        
        logger.info(f"Cleaned up {removed_count} old caches")
