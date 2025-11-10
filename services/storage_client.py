"""
Google Cloud Storage Client
Handles uploading and managing project archives in GCS
"""
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

try:
    from google.cloud import storage
    from google.cloud.exceptions import GoogleCloudError
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    storage = None
    GoogleCloudError = Exception

logger = logging.getLogger(__name__)


class StorageClient:
    """Client for Google Cloud Storage operations"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        bucket_name: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize Storage Client
        
        Args:
            project_id: Google Cloud project ID
            bucket_name: GCS bucket name for archives
            enabled: Whether GCS integration is enabled
        """
        self.enabled = enabled and GCS_AVAILABLE
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.client = None
        self.bucket = None
        
        if not self.enabled:
            if not GCS_AVAILABLE:
                logger.warning(
                    "Google Cloud Storage library not available. "
                    "Install with: pip install google-cloud-storage"
                )
            else:
                logger.info("Google Cloud Storage integration disabled")
            return
        
        if not project_id or not bucket_name:
            logger.warning(
                "GCS project_id or bucket_name not provided. "
                "Storage features will be disabled."
            )
            self.enabled = False
            return
        
        try:
            # Initialize GCS client
            self.client = storage.Client(project=project_id)
            self.bucket = self.client.bucket(bucket_name)
            
            # Verify bucket exists
            if not self.bucket.exists():
                logger.error(f"GCS bucket does not exist: {bucket_name}")
                self.enabled = False
            else:
                logger.info(
                    f"StorageClient initialized for project {project_id}, "
                    f"bucket {bucket_name}"
                )
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            self.enabled = False
    
    def upload_archive(
        self,
        local_path: str,
        project_id: str,
        folder: str = "archives"
    ) -> Optional[str]:
        """
        Upload project archive to GCS
        
        Args:
            local_path: Path to local ZIP file
            project_id: Project identifier
            folder: GCS folder/prefix for the file
            
        Returns:
            Public URL of uploaded file, or None if upload fails
        """
        if not self.enabled:
            logger.debug("GCS not enabled, skipping upload")
            return None
        
        local_file = Path(local_path)
        
        if not local_file.exists():
            logger.error(f"Local file not found: {local_path}")
            return None
        
        try:
            # Create blob name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"{folder}/{project_id}_{timestamp}.zip"
            
            # Upload file
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(local_path)
            
            # Set metadata
            blob.metadata = {
                "project_id": project_id,
                "uploaded_at": datetime.now().isoformat()
            }
            blob.patch()
            
            # Generate signed URL (valid for 1 hour)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET"
            )
            
            logger.info(f"Uploaded archive to GCS: {blob_name}")
            return url
            
        except GoogleCloudError as e:
            logger.error(f"GCS upload failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during GCS upload: {str(e)}")
            return None
    
    def delete_archive(self, blob_name: str) -> bool:
        """
        Delete archive from GCS
        
        Args:
            blob_name: Name of blob to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted archive from GCS: {blob_name}")
            return True
        except GoogleCloudError as e:
            logger.error(f"Failed to delete GCS blob {blob_name}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting GCS blob: {str(e)}")
            return False
    
    def list_archives(self, prefix: str = "archives/") -> list:
        """
        List archives in GCS bucket
        
        Args:
            prefix: Prefix to filter blobs
            
        Returns:
            List of blob names
        """
        if not self.enabled:
            return []
        
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]
        except GoogleCloudError as e:
            logger.error(f"Failed to list GCS blobs: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing GCS blobs: {str(e)}")
            return []
    
    def cleanup_old_archives(self, max_age_days: int = 7) -> int:
        """
        Delete archives older than specified age
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of archives deleted
        """
        if not self.enabled:
            return 0
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix="archives/")
            
            for blob in blobs:
                # Check blob creation time
                if blob.time_created and blob.time_created.replace(tzinfo=None) < cutoff_time:
                    try:
                        blob.delete()
                        deleted_count += 1
                        logger.debug(f"Deleted old archive: {blob.name}")
                    except Exception as e:
                        logger.error(f"Failed to delete blob {blob.name}: {str(e)}")
            
            if deleted_count > 0:
                logger.info(
                    f"Cleaned up {deleted_count} old archives "
                    f"(older than {max_age_days} days)"
                )
            
            return deleted_count
            
        except GoogleCloudError as e:
            logger.error(f"Failed to cleanup old archives: {str(e)}")
            return deleted_count
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {str(e)}")
            return deleted_count
    
    def is_enabled(self) -> bool:
        """
        Check if GCS integration is enabled and working
        
        Returns:
            True if enabled, False otherwise
        """
        return self.enabled
