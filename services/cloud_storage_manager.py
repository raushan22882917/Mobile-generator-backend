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
            bucket_name: GCS bucket name
            project_id: Google Cloud project ID (optional)
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.client = None
        self.bucket = None
        
        if bucket_name:
            try:
                self.client = storage.Client(project=project_id)
                self.bucket = self.client.bucket(bucket_name)
                logger.info(f"Cloud Storage initialized: {bucket_name}")
            except Exception as e:
                logger.warning(f"Cloud Storage not available: {e}")
    
    def is_available(self) -> bool:
        """Check if Cloud Storage is available"""
        return self.client is not None and self.bucket is not None
    
    async def upload_project(self, project_id: str, project_dir: str) -> Optional[str]:
        """
        Upload project directory to Cloud Storage
        
        Args:
            project_id: Project identifier
            project_dir: Local project directory path
            
        Returns:
            GCS path or None if failed
        """
        if not self.is_available():
            logger.warning("Cloud Storage not available, skipping upload")
            return None
        
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
        """
        if not self.is_available():
            logger.warning("Cloud Storage not available")
            return False
        
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
        """Create ZIP file from directory"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Skip node_modules and other large folders
                dirs[:] = [d for d in dirs if d not in ['node_modules', '.expo', '.git']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
    
    async def list_projects(self) -> list:
        """List all projects in Cloud Storage"""
        if not self.is_available():
            return []
        
        try:
            blobs = self.bucket.list_blobs(prefix="projects/")
            return [blob.name.replace("projects/", "").replace(".zip", "") 
                    for blob in blobs]
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete project from Cloud Storage"""
        if not self.is_available():
            return False
        
        try:
            blob_name = f"projects/{project_id}.zip"
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Project {project_id} deleted from Cloud Storage")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return False
