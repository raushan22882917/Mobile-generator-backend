"""File Management Service for Editor"""
import os
import shutil
from typing import Optional, Dict, Any
from pathlib import Path

class FileManager:
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir
    
    def get_project_path(self, project_id: str) -> str:
        """Get full path to project directory"""
        return os.path.join(self.projects_dir, project_id)
    
    def read_file(self, project_id: str, file_path: str) -> Optional[str]:
        """Read file content"""
        full_path = os.path.join(self.get_project_path(project_id), file_path)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def write_file(self, project_id: str, file_path: str, content: str) -> bool:
        """Write content to file"""
        full_path = os.path.join(self.get_project_path(project_id), file_path)
        
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Touch a watch file to trigger Metro bundler reload
            self._trigger_reload(project_id)
            
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    
    def _trigger_reload(self, project_id: str):
        """Trigger Metro bundler reload by touching a file"""
        try:
            import time
            project_path = self.get_project_path(project_id)
            # Touch app.json to trigger reload
            app_json = os.path.join(project_path, 'app.json')
            if os.path.exists(app_json):
                # Update modification time
                os.utime(app_json, None)
        except Exception as e:
            print(f"Error triggering reload: {e}")
    
    def create_file(self, project_id: str, file_path: str, content: str = "") -> bool:
        """Create a new file"""
        result = self.write_file(project_id, file_path, content)
        if result:
            self._trigger_reload(project_id)
        return result
    
    def create_folder(self, project_id: str, folder_path: str) -> bool:
        """Create a new folder"""
        full_path = os.path.join(self.get_project_path(project_id), folder_path)
        
        try:
            os.makedirs(full_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating folder: {e}")
            return False
    
    def delete_file(self, project_id: str, file_path: str) -> bool:
        """Delete a file"""
        full_path = os.path.join(self.get_project_path(project_id), file_path)
        
        if not os.path.exists(full_path):
            return False
        
        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
            
            # Trigger reload
            self._trigger_reload(project_id)
            
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def rename_file(self, project_id: str, old_path: str, new_name: str) -> bool:
        """Rename a file or folder"""
        old_full_path = os.path.join(self.get_project_path(project_id), old_path)
        
        if not os.path.exists(old_full_path):
            return False
        
        # Get directory and create new path
        directory = os.path.dirname(old_full_path)
        new_full_path = os.path.join(directory, new_name)
        
        try:
            os.rename(old_full_path, new_full_path)
            
            # Trigger reload
            self._trigger_reload(project_id)
            
            return True
        except Exception as e:
            print(f"Error renaming file: {e}")
            return False
    
    def list_files(self, project_id: str, directory: str = "") -> Dict[str, Any]:
        """List files in a directory"""
        full_path = os.path.join(self.get_project_path(project_id), directory)
        
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return {"files": [], "folders": []}
        
        files = []
        folders = []
        
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                
                if os.path.isfile(item_path):
                    files.append({
                        "name": item,
                        "path": os.path.join(directory, item) if directory else item,
                        "size": os.path.getsize(item_path)
                    })
                elif os.path.isdir(item_path):
                    folders.append({
                        "name": item,
                        "path": os.path.join(directory, item) if directory else item
                    })
            
            return {"files": files, "folders": folders}
        except Exception as e:
            print(f"Error listing files: {e}")
            return {"files": [], "folders": []}
