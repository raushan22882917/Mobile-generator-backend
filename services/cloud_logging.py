"""
Google Cloud Logging Service
Fetches logs from Google Cloud Logging API for projects
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from google.cloud import logging as cloud_logging
    from google.cloud.logging import Client
    from google.cloud.exceptions import GoogleCloudError
    CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    CLOUD_LOGGING_AVAILABLE = False
    cloud_logging = None
    Client = None
    GoogleCloudError = Exception

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: str
    severity: str
    message: str
    resource_type: str
    labels: Dict[str, str]


class CloudLoggingService:
    """Service for fetching logs from Google Cloud Logging"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize Cloud Logging Service
        
        Args:
            project_id: Google Cloud project ID
            enabled: Whether Cloud Logging integration is enabled
        """
        self.enabled = enabled and CLOUD_LOGGING_AVAILABLE
        self.project_id = project_id
        self.client = None
        
        if not self.enabled:
            if not CLOUD_LOGGING_AVAILABLE:
                logger.warning(
                    "Google Cloud Logging library not available. "
                    "Install with: pip install google-cloud-logging"
                )
            else:
                logger.info("Google Cloud Logging integration disabled")
            return
        
        if not project_id:
            logger.warning(
                "GCP project_id not provided. "
                "Cloud Logging features will be disabled."
            )
            self.enabled = False
            return
        
        try:
            # Initialize Cloud Logging client
            self.client = Client(project=project_id)
            logger.info(
                f"CloudLoggingService initialized for project {project_id}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Logging client: {str(e)}")
            self.enabled = False
    
    def get_project_logs(
        self,
        project_id: str,
        hours: int = 24,
        limit: int = 1000,
        severity: Optional[str] = None
    ) -> List[LogEntry]:
        """
        Get logs for a specific project from Google Cloud
        
        Args:
            project_id: Project identifier to filter logs
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of log entries to return (default: 1000)
            severity: Filter by severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            List of LogEntry objects
        """
        if not self.enabled or not self.client:
            logger.debug("Cloud Logging not enabled, returning empty logs")
            return []
        
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Build filter query
            # Filter by Cloud Run service logs and Cloud Build logs
            # Use OR for resource types, AND for other conditions
            resource_filter = '(resource.type="cloud_run_revision" OR resource.type="build")'
            
            filter_parts = [
                f'timestamp >= "{start_time.isoformat()}Z"',
                f'timestamp <= "{end_time.isoformat()}Z"',
                resource_filter,
                # Filter by project ID if it appears in labels or text
                f'(jsonPayload.project_id="{project_id}" OR textPayload=~".*{project_id}.*" OR labels.project_id="{project_id}")'
            ]
            
            if severity:
                filter_parts.append(f'severity >= "{severity}"')
            
            filter_query = ' AND '.join(filter_parts)
            
            logger.info(
                f"Fetching logs for project {project_id} "
                f"from last {hours} hours"
            )
            
            # Fetch logs
            entries = self.client.list_entries(
                filter_=filter_query,
                max_results=limit,
                order_by=cloud_logging.DESCENDING
            )
            
            log_entries = []
            for entry in entries:
                # Extract log data
                timestamp = entry.timestamp.isoformat() if entry.timestamp else ""
                severity = entry.severity or "INFO"
                resource_type = entry.resource.type if entry.resource else "unknown"
                
                # Get message from payload
                message = ""
                if entry.payload:
                    if isinstance(entry.payload, dict):
                        # JSON payload
                        message = entry.payload.get('message', str(entry.payload))
                        if not message or message == str(entry.payload):
                            message = entry.payload.get('textPayload', str(entry.payload))
                    else:
                        # Text payload
                        message = str(entry.payload)
                
                # Get labels
                labels = {}
                if entry.labels:
                    labels = dict(entry.labels)
                if entry.resource and entry.resource.labels:
                    labels.update(dict(entry.resource.labels))
                
                log_entries.append(LogEntry(
                    timestamp=timestamp,
                    severity=severity,
                    message=message,
                    resource_type=resource_type,
                    labels=labels
                ))
            
            logger.info(f"Retrieved {len(log_entries)} log entries for project {project_id}")
            return log_entries
            
        except GoogleCloudError as e:
            logger.error(f"Google Cloud Logging error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching logs: {str(e)}", exc_info=True)
            return []
    
    def get_service_logs(
        self,
        service_name: str,
        hours: int = 24,
        limit: int = 1000
    ) -> List[LogEntry]:
        """
        Get logs for a specific Cloud Run service
        
        Args:
            service_name: Cloud Run service name
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of log entries to return (default: 1000)
            
        Returns:
            List of LogEntry objects
        """
        if not self.enabled or not self.client:
            logger.debug("Cloud Logging not enabled, returning empty logs")
            return []
        
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Build filter query for Cloud Run service
            filter_query = (
                f'resource.type="cloud_run_revision" '
                f'AND resource.labels.service_name="{service_name}" '
                f'AND timestamp >= "{start_time.isoformat()}Z" '
                f'AND timestamp <= "{end_time.isoformat()}Z"'
            )
            
            logger.info(
                f"Fetching logs for service {service_name} "
                f"from last {hours} hours"
            )
            
            # Fetch logs
            entries = self.client.list_entries(
                filter_=filter_query,
                max_results=limit,
                order_by=cloud_logging.DESCENDING
            )
            
            log_entries = []
            for entry in entries:
                timestamp = entry.timestamp.isoformat() if entry.timestamp else ""
                severity = entry.severity or "INFO"
                resource_type = entry.resource.type if entry.resource else "unknown"
                
                message = ""
                if entry.payload:
                    if isinstance(entry.payload, dict):
                        message = entry.payload.get('message', str(entry.payload))
                        if not message or message == str(entry.payload):
                            message = entry.payload.get('textPayload', str(entry.payload))
                    else:
                        message = str(entry.payload)
                
                labels = {}
                if entry.labels:
                    labels = dict(entry.labels)
                if entry.resource and entry.resource.labels:
                    labels.update(dict(entry.resource.labels))
                
                log_entries.append(LogEntry(
                    timestamp=timestamp,
                    severity=severity,
                    message=message,
                    resource_type=resource_type,
                    labels=labels
                ))
            
            logger.info(f"Retrieved {len(log_entries)} log entries for service {service_name}")
            return log_entries
            
        except Exception as e:
            logger.error(f"Error fetching service logs: {str(e)}", exc_info=True)
            return []
    
    def get_build_logs(
        self,
        build_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 1000
    ) -> List[LogEntry]:
        """
        Get Cloud Build logs
        
        Args:
            build_id: Optional build ID to filter
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of log entries to return (default: 1000)
            
        Returns:
            List of LogEntry objects
        """
        if not self.enabled or not self.client:
            logger.debug("Cloud Logging not enabled, returning empty logs")
            return []
        
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Build filter query for Cloud Build
            filter_parts = [
                f'resource.type="build"',
                f'timestamp >= "{start_time.isoformat()}Z"',
                f'timestamp <= "{end_time.isoformat()}Z"'
            ]
            
            if build_id:
                filter_parts.append(f'resource.labels.build_id="{build_id}"')
            
            filter_query = ' AND '.join(filter_parts)
            
            logger.info(f"Fetching Cloud Build logs from last {hours} hours")
            
            # Fetch logs
            entries = self.client.list_entries(
                filter_=filter_query,
                max_results=limit,
                order_by=cloud_logging.DESCENDING
            )
            
            log_entries = []
            for entry in entries:
                timestamp = entry.timestamp.isoformat() if entry.timestamp else ""
                severity = entry.severity or "INFO"
                resource_type = entry.resource.type if entry.resource else "unknown"
                
                message = ""
                if entry.payload:
                    if isinstance(entry.payload, dict):
                        message = entry.payload.get('message', str(entry.payload))
                        if not message or message == str(entry.payload):
                            message = entry.payload.get('textPayload', str(entry.payload))
                    else:
                        message = str(entry.payload)
                
                labels = {}
                if entry.labels:
                    labels = dict(entry.labels)
                if entry.resource and entry.resource.labels:
                    labels.update(dict(entry.resource.labels))
                
                log_entries.append(LogEntry(
                    timestamp=timestamp,
                    severity=severity,
                    message=message,
                    resource_type=resource_type,
                    labels=labels
                ))
            
            logger.info(f"Retrieved {len(log_entries)} Cloud Build log entries")
            return log_entries
            
        except Exception as e:
            logger.error(f"Error fetching build logs: {str(e)}", exc_info=True)
            return []

