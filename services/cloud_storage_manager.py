"""
Cloud Storage Manager
Handles uploading/downloading projects to/from Google Cloud Storage
"""
import os
import logging
import zipfile
from pathlib import Path
from typing import Optional
from google.cloud import storage

logger = logging.getLogger(__name__)


class CloudStorageManager:
    """Manages project storage in Google Cloud Storage"""
    
    def __init__(self, bucket_name: str, project_id: str = None):
        """
        Initialize Cloud Storage Manager
        
        Args:
            bucket_name: GCS bucket name (required for production)
            project_id: Google Cloud project ID (required for production)
        
        Note: In Cloud Run, this will use the default service account automatically.
        No service account key file is needed.
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.client = None
        self.bucket = None
        
        if not bucket_name or not project_id:
            logger.warning("Cloud Storage not configured - bucket_name and project_id are required")
            return
            
        try:
            # In Cloud Run, this automatically uses the default service account
            # No credentials file needed!
            self.client = storage.Client(project=project_id)
            self.bucket = self.client.bucket(bucket_name)
            
            # Test bucket access
            if self.bucket.exists():
                logger.info(f"✅ Cloud Storage initialized successfully: {bucket_name}")
            else:
                logger.error(f"❌ Bucket does not exist: {bucket_name}")
                self.client = None
                self.bucket = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cloud Storage: {e}")
            logger.error(f"   Project: {project_id}, Bucket: {bucket_name}")
            self.client = None
            self.bucket = None
    
    def is_available(self) -> bool:
        """Check if Cloud Storage is available"""
        return self.client is not None and self.bucket is not None
    
    async def upload_project(self, project_id: str, project_dir: str) -> str:
        """
        Upload project directory to Cloud Storage
        
        Args:
            project_id: Project identifier
            project_dir: Local project directory path
            
        Returns:
            GCS path
            
        Raises:
            Exception if upload fails
        """
        
        try:
            logger.info(f"Uploading project {project_id} to Cloud Storage")
            
            # Create ZIP file
            zip_path = f"/tmp/{project_id}.zip"
            self._create_zip(project_dir, zip_path)
            
            # Upload to GCS
            blob_name = f"projects/{project_id}.zip"
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(zip_path)
            
            # Clean up local ZIP
            os.remove(zip_path)
            
            gcs_path = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"Project uploaded: {gcs_path}")
            
            return gcs_path
            
        except Exception as e:
            logger.error(f"Failed to upload project: {e}")
            return None
    
    async def download_project(self, project_id: str, target_dir: str) -> bool:
        """
        Download project from Cloud Storage
        
        Args:
            project_id: Project identifier
            target_dir: Local directory to extract to
            
        Returns:
            True if successful
            
        Raises:
            Exception if download fails
        """
        
        try:
            logger.info(f"Downloading project {project_id} from Cloud Storage")
            
            # Download ZIP
            blob_name = f"projects/{project_id}.zip"
            blob = self.bucket.blob(blob_name)
            
            zip_path = f"/tmp/{project_id}.zip"
            blob.download_to_filename(zip_path)
            
            # Extract
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # Clean up ZIP
            os.remove(zip_path)
            
            logger.info(f"Project downloaded to {target_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download project: {e}")
            return False
    
    def _create_zip(self, source_dir: str, zip_path: str):
        """
        Create ZIP file from directory
        
        Excludes node_modules, package-lock.json and build artifacts to save space.
        These will be restored using shared dependencies on download.
        """
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Skip node_modules and other large folders
                # These are excluded to save storage space
                dirs[:] = [d for d in dirs if d not in [
                    'node_modules',  # Will use shared dependencies
                    '.expo',         # Build cache
                    '.git',          # Version control
                    'dist',          # Build output
                    'build',         # Build output
                    '__pycache__'    # Python cache
                ]]
                
                for file in files:
                    # Skip package-lock.json - will be regenerated with shared deps
                    if file in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']:
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
    
    async def list_projects(self) -> list:
        """
        List all projects in Cloud Storage
        
        Returns:
            List of project IDs
            
        Raises:
            Exception if listing fails
        """
        try:
            blobs = self.bucket.list_blobs(prefix="projects/")
            return [blob.name.replace("projects/", "").replace(".zip", "") 
                    for blob in blobs if blob.name.endswith(".zip")]
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise
    
    async def get_project_metadata(self, project_id: str) -> dict:
        """
        Get project metadata from Cloud Storage
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dictionary with metadata (created_at, last_active, size, etc.)
            
        Raises:
            Exception if metadata retrieval fails
        """
        try:
            blob_name = f"projects/{project_id}.zip"
            blob = self.bucket.blob(blob_name)
            
            # Reload to get latest metadata
            blob.reload()
            
            return {
                "project_id": project_id,
                "created_at": blob.time_created.isoformat() if blob.time_created else None,
                "last_active": blob.updated.isoformat() if blob.updated else None,
                "size_bytes": blob.size,
                "size_mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
                "content_type": blob.content_type,
                "prompt": f"Project {project_id[:8]}",  # We don't store prompt in metadata yet
                "storage_class": blob.storage_class
            }
        except Exception as e:
            logger.warning(f"Failed to get metadata for project {project_id}: {e}")
            # Return default metadata if blob doesn't exist or error occurs
            from datetime import datetime
            return {
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "size_bytes": 0,
                "size_mb": 0,
                "prompt": f"Project {project_id[:8]}"
            }
    
    async def delete_project(self, project_id: str) -> bool:
        """
        Delete project from Cloud Storage
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if successful
            
        Raises:
            Exception if deletion fails
        """
        try:
            blob_name = f"projects/{project_id}.zip"
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Project {project_id} deleted from Cloud Storage")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            raise
