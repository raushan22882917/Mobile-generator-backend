"""
Resource Monitor Service
Tracks system resource usage and manages capacity
"""
import logging
import psutil
from datetime import datetime, timedelta
from typing import Optional

from models.project import SystemMetrics

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Service for monitoring system resources and managing capacity"""
    
    def __init__(
        self,
        max_projects: int = 10,
        max_cpu_percent: float = 80.0,
        max_memory_percent: float = 80.0,
        min_disk_percent: float = 10.0
    ):
        """
        Initialize ResourceMonitor
        
        Args:
            max_projects: Maximum concurrent projects allowed
            max_cpu_percent: Maximum CPU usage threshold (%)
            max_memory_percent: Maximum memory usage threshold (%)
            min_disk_percent: Minimum free disk space threshold (%)
        """
        self.max_projects = max_projects
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.min_disk_percent = min_disk_percent
        
        # Track metrics
        self.total_projects_created = 0
        self.generation_times = []
        
        logger.info(
            f"ResourceMonitor initialized with max_projects={max_projects}, "
            f"max_cpu={max_cpu_percent}%, max_memory={max_memory_percent}%, "
            f"min_disk={min_disk_percent}%"
        )
    
    def get_system_metrics(self, active_projects: int) -> SystemMetrics:
        """
        Get current system resource usage metrics
        
        Args:
            active_projects: Number of currently active projects
            
        Returns:
            SystemMetrics with current resource usage
        """
        try:
            # Get CPU usage (averaged over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage for current working directory
            disk = psutil.disk_usage('.')
            disk_percent = disk.percent
            
            # Calculate average generation time
            avg_generation_time = (
                sum(self.generation_times) / len(self.generation_times)
                if self.generation_times else 0.0
            )
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                active_projects=active_projects,
                total_projects_created=self.total_projects_created,
                average_generation_time=avg_generation_time
            )
            
            logger.debug(
                f"System metrics: CPU={cpu_percent}%, Memory={memory_percent}%, "
                f"Disk={disk_percent}%, Active={active_projects}"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            # Return default metrics on error
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                active_projects=active_projects,
                total_projects_created=self.total_projects_created,
                average_generation_time=0.0
            )
    
    def record_project_creation(self, generation_time: Optional[float] = None) -> None:
        """
        Record a new project creation
        
        Args:
            generation_time: Optional time taken to generate project (seconds)
        """
        self.total_projects_created += 1
        
        if generation_time is not None and generation_time > 0:
            self.generation_times.append(generation_time)
            # Keep only last 100 generation times
            if len(self.generation_times) > 100:
                self.generation_times = self.generation_times[-100:]
        
        logger.debug(f"Recorded project creation (total: {self.total_projects_created})")
    
    def can_accept_new_project(self, active_projects: int) -> tuple[bool, Optional[str]]:
        """
        Check if system has capacity to accept a new project
        
        Args:
            active_projects: Number of currently active projects
            
        Returns:
            Tuple of (can_accept, reason) where reason is None if can accept,
            otherwise contains the reason for rejection
        """
        # Check project count limit
        if active_projects >= self.max_projects:
            reason = f"Maximum concurrent projects limit reached ({self.max_projects})"
            logger.warning(f"Cannot accept new project: {reason}")
            return False, reason
        
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_percent:
                reason = f"Memory usage too high ({memory.percent:.1f}% > {self.max_memory_percent}%)"
                logger.warning(f"Cannot accept new project: {reason}")
                return False, reason
            
            # Check disk space
            disk = psutil.disk_usage('.')
            free_percent = 100 - disk.percent
            if free_percent < self.min_disk_percent:
                reason = f"Disk space too low ({free_percent:.1f}% < {self.min_disk_percent}%)"
                logger.warning(f"Cannot accept new project: {reason}")
                return False, reason
            
            # Check CPU usage (optional warning, not blocking)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self.max_cpu_percent:
                logger.warning(
                    f"CPU usage high ({cpu_percent:.1f}% > {self.max_cpu_percent}%), "
                    "but accepting project"
                )
            
            logger.debug("System has capacity for new project")
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking system capacity: {str(e)}")
            # On error, allow project creation (fail open)
            return True, None
    
    def cleanup_inactive_projects(
        self,
        project_manager,
        max_age_minutes: int = 30
    ) -> int:
        """
        Cleanup projects that have been inactive for specified duration
        
        Args:
            project_manager: ProjectManager instance to perform cleanup
            max_age_minutes: Maximum age in minutes before cleanup
            
        Returns:
            Number of projects cleaned up
        """
        try:
            cleanup_count = project_manager.cleanup_old_projects(max_age_minutes)
            
            if cleanup_count > 0:
                logger.info(
                    f"Cleaned up {cleanup_count} inactive projects "
                    f"(older than {max_age_minutes} minutes)"
                )
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during cleanup of inactive projects: {str(e)}")
            return 0
    
    def cleanup_by_disk_space(
        self,
        project_manager
    ) -> int:
        """
        Cleanup oldest projects when disk space is low
        
        Args:
            project_manager: ProjectManager instance to perform cleanup
            
        Returns:
            Number of projects cleaned up
        """
        try:
            disk = psutil.disk_usage('.')
            free_percent = 100 - disk.percent
            
            # Only cleanup if disk space is below threshold
            if free_percent >= self.min_disk_percent:
                return 0
            
            logger.warning(
                f"Disk space low ({free_percent:.1f}% free), "
                "cleaning up oldest projects"
            )
            
            # Get all active projects sorted by last_active time
            active_projects = project_manager.list_active_projects()
            if not active_projects:
                return 0
            
            # Sort by last_active (oldest first)
            sorted_projects = sorted(
                active_projects.items(),
                key=lambda x: x[1].last_active
            )
            
            cleanup_count = 0
            # Cleanup oldest projects until disk space is acceptable
            for project_id, project in sorted_projects:
                try:
                    project_manager.cleanup_project(project_id)
                    cleanup_count += 1
                    
                    # Check if we have enough space now
                    disk = psutil.disk_usage('.')
                    free_percent = 100 - disk.percent
                    if free_percent >= self.min_disk_percent + 5:  # Add 5% buffer
                        break
                        
                except Exception as e:
                    logger.error(f"Failed to cleanup project {project_id}: {str(e)}")
            
            logger.info(
                f"Cleaned up {cleanup_count} projects due to low disk space "
                f"(now {free_percent:.1f}% free)"
            )
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during disk space cleanup: {str(e)}")
            return 0
