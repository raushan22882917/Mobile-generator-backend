"""
Project Manager Service
Handles project creation, file management, and cleanup
"""
import os
import shutil
import uuid
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Set
import logging

from models.project import Project, ProjectStatus, GeneratedCode
from services.port_manager import PortManager

logger = logging.getLogger(__name__)


class ProjectManager:
    """Service for managing project lifecycle and file operations"""
    
    def __init__(
        self,
        base_dir: str,
        port_manager: Optional[PortManager] = None,
        max_concurrent_projects: int = 10
    ):
        """
        Initialize ProjectManager
        
        Args:
            base_dir: Base directory for storing project files
            port_manager: Optional PortManager instance (creates default if None)
            max_concurrent_projects: Maximum concurrent projects allowed
        """
        self.base_dir = Path(base_dir)
        self.active_projects: Dict[str, Project] = {}
        self.max_concurrent_projects = max_concurrent_projects
        
        # Initialize or use provided PortManager
        if port_manager is None:
            self.port_manager = PortManager(
                start_port=19006,
                max_ports=max_concurrent_projects
            )
        else:
            self.port_manager = port_manager
        
        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"ProjectManager initialized with base_dir: {self.base_dir}, "
            f"max_concurrent_projects: {max_concurrent_projects}"
        )
    
    def create_project(
        self,
        user_id: str,
        prompt: str
    ) -> Project:
        """
        Create a new project with unique directory and allocated port
        
        Args:
            user_id: User identifier
            prompt: User's app description
            
        Returns:
            Created Project instance
            
        Raises:
            ValueError: If directory collision occurs or max projects reached
        """
        # Check if we can accept new projects
        if not self.can_accept_new_project():
            logger.error(
                f"Cannot create project: maximum concurrent projects "
                f"({self.max_concurrent_projects}) reached"
            )
            raise ValueError(
                f"Maximum concurrent projects limit reached "
                f"({self.max_concurrent_projects}). Please try again later."
            )
        
        # Allocate port for the project
        port = self.port_manager.allocate_port()
        
        try:
            # Generate unique project ID
            project_id = str(uuid.uuid4())
            
            # Create project directory path (will be created by create-expo-app)
            project_dir = self.base_dir / project_id
            
            # Note: Directory will be created by create-expo-app command
            # We just reserve the path here
            logger.info(f"Reserved project directory path: {project_dir}")
            
            # Create Project instance
            project = Project(
                id=project_id,
                user_id=user_id,
                prompt=prompt,
                status=ProjectStatus.INITIALIZING,
                directory=str(project_dir),
                port=port,
                preview_url=None,
                error_message=None,
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            
            # Track active project
            self.active_projects[project_id] = project
            
            logger.info(f"Project created: {project_id} for user {user_id} on port {port}")
            return project
            
        except Exception as e:
            # Release port if project creation fails
            self.port_manager.release_port(port)
            raise
    
    def write_code_files(self, project: Project, code: GeneratedCode) -> None:
        """
        Write generated code files to project directory
        
        Args:
            project: Project instance
            code: GeneratedCode containing files to write
            
        Raises:
            ValueError: If project directory doesn't exist
            IOError: If file writing fails
        """
        project_dir = Path(project.directory)
        
        # Validate project directory exists
        if not project_dir.exists():
            logger.error(f"Project directory not found: {project_dir}")
            raise ValueError(f"Project directory does not exist: {project.directory}")
        
        try:
            # Write each code file (replace existing files from create-expo-app)
            for code_file in code.files:
                file_path = project_dir / code_file.path
                
                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file content
                file_path.write_text(code_file.content, encoding='utf-8')
                logger.debug(f"Wrote file: {file_path}")
            
            # Update package.json to add any additional dependencies
            # IMPORTANT: Ensure essential dependencies (expo, expo-status-bar, @expo/vector-icons) are always present
            package_json_path = project_dir / "package.json"
            if package_json_path.exists():
                # Always ensure essential dependencies are in package.json
                self._ensure_essential_dependencies(package_json_path)
                
                # Add additional dependencies from generated code
                if code.dependencies:
                    self._update_package_json_dependencies(package_json_path, code.dependencies)
            
            # Copy metro.config.js for hot reloading support
            self._copy_metro_config(project_dir)
            
            logger.info(f"Successfully wrote {len(code.files)} files to project {project.id}")
            
        except Exception as e:
            logger.error(f"Failed to write code files for project {project.id}: {str(e)}")
            raise IOError(f"Failed to write code files: {str(e)}")
    
    def _copy_metro_config(self, project_dir: Path) -> None:
        """
        Copy metro.config.js template to project for hot reloading
        
        Args:
            project_dir: Project directory path
        """
        import shutil
        
        try:
            # Get template path
            template_path = Path(__file__).parent.parent / "templates" / "metro.config.js"
            
            if template_path.exists():
                target_path = project_dir / "metro.config.js"
                shutil.copy2(template_path, target_path)
                logger.info(f"Copied metro.config.js to {project_dir}")
            else:
                logger.warning(f"Metro config template not found at {template_path}")
        except Exception as e:
            logger.warning(f"Failed to copy metro config: {e}")
    
    def _ensure_essential_dependencies(self, package_json_path: Path) -> None:
        """
        Ensure essential dependencies are in package.json.
        Essential dependencies: expo, expo-status-bar, @expo/vector-icons
        
        Args:
            package_json_path: Path to package.json file
        """
        import json
        
        try:
            # Read existing package.json
            package_json = json.loads(package_json_path.read_text(encoding='utf-8'))
            
            # Ensure dependencies section exists
            if "dependencies" not in package_json:
                package_json["dependencies"] = {}
            
            # Essential dependencies that should always be present
            essential_deps = {
                "expo": "latest",
                "expo-status-bar": "latest",
                "@expo/vector-icons": "^15.0.0"  # Always include vector icons for professional UI
            }
            
            updated = False
            for dep_name, dep_version in essential_deps.items():
                if dep_name not in package_json["dependencies"]:
                    logger.info(f"Adding essential dependency: {dep_name}@{dep_version}")
                    package_json["dependencies"][dep_name] = dep_version
                    updated = True
                else:
                    # Verify version is valid
                    current_version = package_json["dependencies"].get(dep_name, "")
                    if current_version == "*" or current_version == "":
                        logger.warning(f"{dep_name} version is invalid ({current_version}), updating to {dep_version}")
                        package_json["dependencies"][dep_name] = dep_version
                        updated = True
            
            if updated:
                # Write updated package.json
                package_json_path.write_text(json.dumps(package_json, indent=2), encoding='utf-8')
                logger.info("Updated package.json with essential dependencies (expo, expo-status-bar, @expo/vector-icons)")
            else:
                logger.debug("All essential dependencies already present in package.json")
                
        except Exception as e:
            logger.error(f"Failed to ensure essential dependencies in package.json: {e}")
            # Don't fail the whole process if this fails
    
    def _update_package_json_dependencies(self, package_json_path: Path, dependencies: list) -> None:
        """
        Update package.json to add additional dependencies
        
        Args:
            package_json_path: Path to package.json file
            dependencies: List of dependency names to add
        """
        import json
        
        try:
            # Read existing package.json
            package_json = json.loads(package_json_path.read_text(encoding='utf-8'))
            
            # Add new dependencies
            if "dependencies" not in package_json:
                package_json["dependencies"] = {}
            
            for dep in dependencies:
                if dep and dep.strip():
                    clean_dep = dep.strip()
                    if clean_dep not in package_json["dependencies"]:
                        package_json["dependencies"][clean_dep] = "latest"
                        logger.debug(f"Added dependency: {clean_dep}")
            
            # Write updated package.json
            package_json_path.write_text(json.dumps(package_json, indent=2), encoding='utf-8')
            logger.info(f"Updated package.json with {len(dependencies)} additional dependencies")
            
        except Exception as e:
            logger.error(f"Failed to update package.json: {e}")
            # Don't fail the whole process if this fails
    
    def _create_package_json(self, project_dir: Path, code: GeneratedCode) -> None:
        """
        Create package.json file for Expo project
        
        Args:
            project_dir: Project directory path
            code: GeneratedCode with dependencies
        """
        # Build dependencies object
        dependencies = {
            "expo": f"~{code.expo_version}",
            "react": "18.2.0",
            "react-native": "0.73.0"
        }
        
        # Add custom dependencies from generated code
        for dep in code.dependencies:
            if dep and dep.strip():
                dependencies[dep.strip()] = "latest"
        
        package_json = {
            "name": "expo-app",
            "version": "1.0.0",
            "main": "node_modules/expo/AppEntry.js",
            "scripts": {
                "start": "expo start",
                "android": "expo start --android",
                "ios": "expo start --ios",
                "web": "expo start --web"
            },
            "dependencies": dependencies,
            "devDependencies": {
                "@babel/core": "^7.20.0"
            },
            "private": True
        }
        
        import json
        package_json_path = project_dir / "package.json"
        package_json_path.write_text(json.dumps(package_json, indent=2), encoding='utf-8')
        logger.debug(f"Created package.json with {len(dependencies)} dependencies")
    
    def _create_app_json(self, project_dir: Path, project_id: str) -> None:
        """
        Create app.json configuration file
        
        Args:
            project_dir: Project directory path
            project_id: Project identifier
        """
        app_json = {
            "expo": {
                "name": f"expo-app-{project_id[:8]}",
                "slug": f"expo-app-{project_id[:8]}",
                "version": "1.0.0",
                "orientation": "portrait",
                "icon": "./assets/icon.png",
                "userInterfaceStyle": "light",
                "splash": {
                    "image": "./assets/splash.png",
                    "resizeMode": "contain",
                    "backgroundColor": "#ffffff"
                },
                "assetBundlePatterns": [
                    "**/*"
                ],
                "ios": {
                    "supportsTablet": True
                },
                "android": {
                    "adaptiveIcon": {
                        "foregroundImage": "./assets/adaptive-icon.png",
                        "backgroundColor": "#ffffff"
                    }
                },
                "web": {
                    "favicon": "./assets/favicon.png"
                }
            }
        }
        
        import json
        app_json_path = project_dir / "app.json"
        app_json_path.write_text(json.dumps(app_json, indent=2), encoding='utf-8')
        logger.debug("Created app.json configuration")
    
    def _create_babel_config(self, project_dir: Path) -> None:
        """
        Create babel.config.js file
        
        Args:
            project_dir: Project directory path
        """
        babel_config = """module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
  };
};
"""
        babel_config_path = project_dir / "babel.config.js"
        babel_config_path.write_text(babel_config, encoding='utf-8')
        logger.debug("Created babel.config.js")
    
    def _create_gitignore(self, project_dir: Path) -> None:
        """
        Create .gitignore file
        
        Args:
            project_dir: Project directory path
        """
        gitignore_content = """node_modules/
.expo/
dist/
npm-debug.*
*.jks
*.p8
*.p12
*.key
*.mobileprovision
*.orig.*
web-build/
.env.local
.env.development.local
.env.test.local
.env.production.local
"""
        gitignore_path = project_dir / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding='utf-8')
        logger.debug("Created .gitignore")
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get project by ID - loads from disk if not in active projects
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project instance or None if not found
        """
        # Check active projects first
        if project_id in self.active_projects:
            return self.active_projects[project_id]
        
        # Try to load from disk
        project_dir = self.base_dir / project_id
        if project_dir.exists() and project_dir.is_dir():
            # Check if it's a valid Expo project
            package_json = project_dir / "package.json"
            if package_json.exists():
                # Load project from disk
                try:
                    created_time = datetime.fromtimestamp(os.path.getctime(str(project_dir)))
                    modified_time = datetime.fromtimestamp(os.path.getmtime(str(project_dir)))
                    
                    # Create project instance for inactive project
                    project = Project(
                        id=project_id,
                        user_id="unknown",
                        prompt="Project loaded from disk",
                        status=ProjectStatus.READY,  # Assume ready since it exists
                        directory=str(project_dir),
                        port=0,  # No active port
                        preview_url=None,
                        error_message=None,
                        created_at=created_time,
                        last_active=modified_time
                    )
                    
                    logger.info(f"Loaded inactive project {project_id} from disk")
                    return project
                except Exception as e:
                    logger.error(f"Failed to load project {project_id} from disk: {e}")
                    return None
        
        return None
    
    def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update project status
        
        Args:
            project_id: Project identifier
            status: New status
            error_message: Optional error message
        """
        project = self.active_projects.get(project_id)
        if project:
            project.status = status
            project.last_active = datetime.now()
            if error_message:
                project.error_message = error_message
            logger.info(f"Project {project_id} status updated to {status.value}")
    
    def update_preview_url(self, project_id: str, preview_url: str, port: Optional[int] = None) -> None:
        """
        Update project preview URL and store in tunnel URLs list with metadata
        
        Args:
            project_id: Project identifier
            preview_url: Public preview URL
            port: Optional port number for the tunnel
        """
        project = self.active_projects.get(project_id)
        if project:
            # Use the new method to add tunnel URL with metadata
            project.add_tunnel_url(preview_url, port=port)
            logger.info(f"Project {project_id} tunnel URL added: {preview_url} (port: {port})")
            # Persist project data to file
            self._persist_project(project)
    
    def _persist_project(self, project: Project) -> None:
        """
        Persist project data to JSON file for long-term storage
        
        Args:
            project: Project instance to persist
        """
        try:
            import json
            projects_dir = self.base_dir / "metadata"
            projects_dir.mkdir(exist_ok=True)
            
            project_file = projects_dir / f"{project.id}.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, indent=2, default=str)
            
            logger.debug(f"Persisted project {project.id} to {project_file}")
        except Exception as e:
            logger.warning(f"Failed to persist project {project.id}: {e}")
    
    def load_project_metadata(self, project_id: str) -> Optional[dict]:
        """
        Load project metadata from persisted file
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project metadata dictionary or None if not found
        """
        try:
            import json
            projects_dir = self.base_dir / "metadata"
            project_file = projects_dir / f"{project_id}.json"
            
            if project_file.exists():
                with open(project_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load project metadata {project_id}: {e}")
        
        return None
    
    def cleanup_project(self, project_id: str) -> None:
        """
        Remove project files and cleanup resources
        
        Args:
            project_id: Project identifier to cleanup
        """
        project = self.active_projects.get(project_id)
        
        if not project:
            logger.warning(f"Attempted to cleanup non-existent project: {project_id}")
            return
        
        project_dir = Path(project.directory)
        
        # Remove project directory and all contents
        if project_dir.exists():
            try:
                shutil.rmtree(project_dir)
                logger.info(f"Removed project directory: {project_dir}")
            except Exception as e:
                logger.error(f"Failed to remove project directory {project_dir}: {str(e)}")
                raise IOError(f"Failed to cleanup project {project_id}: {str(e)}")
        
        # Release allocated port
        self.port_manager.release_port(project.port)
        
        # Remove from active projects
        del self.active_projects[project_id]
        logger.info(f"Project {project_id} cleaned up successfully")
    
    def archive_project(self, project_id: str, output_dir: Optional[Path] = None) -> str:
        """
        Create ZIP archive of project excluding node_modules
        
        Args:
            project_id: Project identifier to archive
            output_dir: Optional directory for archive (defaults to base_dir)
            
        Returns:
            Path to created ZIP file
            
        Raises:
            ValueError: If project not found
            IOError: If archiving fails
        """
        project = self.active_projects.get(project_id)
        
        if not project:
            logger.error(f"Cannot archive non-existent project: {project_id}")
            raise ValueError(f"Project not found: {project_id}")
        
        project_dir = Path(project.directory)
        
        if not project_dir.exists():
            logger.error(f"Project directory not found: {project_dir}")
            raise ValueError(f"Project directory does not exist: {project.directory}")
        
        # Determine output location
        if output_dir is None:
            output_dir = self.base_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create archive filename
        archive_name = f"{project_id}.zip"
        archive_path = output_dir / archive_name
        
        try:
            # Create ZIP archive
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through project directory
                for root, dirs, files in os.walk(project_dir):
                    # Exclude node_modules and other build artifacts
                    dirs[:] = [d for d in dirs if d not in [
                        'node_modules',
                        '.expo',
                        '.expo-shared',
                        'build',
                        'dist',
                        '__pycache__',
                        '.git'
                    ]]
                    
                    for file in files:
                        file_path = Path(root) / file
                        # Calculate relative path for archive
                        arcname = file_path.relative_to(project_dir)
                        zipf.write(file_path, arcname)
            
            logger.info(f"Created archive for project {project_id}: {archive_path}")
            return str(archive_path)
            
        except Exception as e:
            logger.error(f"Failed to archive project {project_id}: {str(e)}")
            # Clean up partial archive if it exists
            if archive_path.exists():
                archive_path.unlink()
            raise IOError(f"Failed to create archive: {str(e)}")
    
    def cleanup_old_projects(self, max_age_minutes: int = 30) -> int:
        """
        Automatically cleanup projects older than specified age
        
        Args:
            max_age_minutes: Maximum age in minutes before cleanup
            
        Returns:
            Number of projects cleaned up
        """
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        projects_to_cleanup = []
        
        # Find projects older than cutoff time
        for project_id, project in self.active_projects.items():
            if project.last_active < cutoff_time:
                projects_to_cleanup.append(project_id)
        
        # Cleanup old projects
        cleanup_count = 0
        for project_id in projects_to_cleanup:
            try:
                self.cleanup_project(project_id)
                cleanup_count += 1
            except Exception as e:
                logger.error(f"Failed to cleanup old project {project_id}: {str(e)}")
        
        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} old projects (older than {max_age_minutes} minutes)")
        
        return cleanup_count
    
    def get_active_project_count(self) -> int:
        """
        Get count of active projects
        
        Returns:
            Number of active projects
        """
        return len(self.active_projects)
    
    def list_active_projects(self) -> Dict[str, Project]:
        """
        Get all active projects
        
        Returns:
            Dictionary of active projects
        """
        return self.active_projects.copy()
    
    def can_accept_new_project(self) -> bool:
        """
        Check if system can accept a new project
        
        Returns:
            True if new project can be created, False otherwise
        """
        return (
            len(self.active_projects) < self.max_concurrent_projects and
            self.port_manager.can_allocate()
        )
    
    def reactivate_project(self, project_id: str) -> Project:
        """
        Reactivate an inactive project by allocating a port and adding to active projects
        
        Args:
            project_id: Project identifier to reactivate
            
        Returns:
            Reactivated Project instance
            
        Raises:
            ValueError: If project not found or cannot be reactivated
        """
        # Check if already active
        if project_id in self.active_projects:
            logger.info(f"Project {project_id} is already active")
            return self.active_projects[project_id]
        
        # Check if we can accept new projects
        if not self.can_accept_new_project():
            raise ValueError("Cannot reactivate project: maximum concurrent projects limit reached")
        
        # Load project from disk
        project_dir = self.base_dir / project_id
        if not project_dir.exists() or not project_dir.is_dir():
            raise ValueError(f"Project directory not found: {project_id}")
        
        package_json = project_dir / "package.json"
        if not package_json.exists():
            raise ValueError(f"Invalid project: package.json not found in {project_id}")
        
        # Allocate a new port
        port = self.port_manager.allocate_port()
        
        try:
            created_time = datetime.fromtimestamp(os.path.getctime(str(project_dir)))
            
            # Create active project instance
            project = Project(
                id=project_id,
                user_id="reactivated",
                prompt="Project reactivated from disk",
                status=ProjectStatus.STARTING_SERVER,
                directory=str(project_dir),
                port=port,
                preview_url=None,
                error_message=None,
                created_at=created_time,
                last_active=datetime.now()
            )
            
            # Add to active projects
            self.active_projects[project_id] = project
            
            logger.info(f"Reactivated project {project_id} on port {port}")
            return project
            
        except Exception as e:
            # Release port if reactivation fails
            self.port_manager.release_port(port)
            raise ValueError(f"Failed to reactivate project: {str(e)}")
