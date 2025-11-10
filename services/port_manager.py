"""
Port Manager Service
Handles port allocation for concurrent project instances
"""
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)


class PortAllocationError(Exception):
    """Raised when port allocation fails"""
    pass


class PortManager:
    """Service for managing port allocation for concurrent projects"""
    
    def __init__(self, start_port: int = 19006, max_ports: int = 100):
        """
        Initialize PortManager
        
        Args:
            start_port: Starting port number for allocation
            max_ports: Maximum number of ports to allocate
        """
        self.start_port = start_port
        self.max_ports = max_ports
        self.allocated_ports: Set[int] = set()
        logger.info(
            f"PortManager initialized: start_port={start_port}, "
            f"max_ports={max_ports}"
        )
    
    def allocate_port(self) -> int:
        """
        Allocate an available port
        
        Returns:
            Allocated port number
            
        Raises:
            PortAllocationError: If no ports available
        """
        # Check if we've reached maximum concurrent projects
        if len(self.allocated_ports) >= self.max_ports:
            logger.error(
                f"Maximum concurrent projects reached: {self.max_ports}"
            )
            raise PortAllocationError(
                f"Maximum concurrent projects limit reached ({self.max_ports}). "
                "Please try again later."
            )
        
        # Find first available port
        for offset in range(self.max_ports):
            port = self.start_port + offset
            if port not in self.allocated_ports:
                self.allocated_ports.add(port)
                logger.info(f"Allocated port {port} (total allocated: {len(self.allocated_ports)})")
                return port
        
        # This should never happen if max_ports check works correctly
        logger.error("Failed to find available port despite capacity check")
        raise PortAllocationError("Failed to allocate port")
    
    def release_port(self, port: int) -> None:
        """
        Release a previously allocated port
        
        Args:
            port: Port number to release
        """
        if port in self.allocated_ports:
            self.allocated_ports.remove(port)
            logger.info(f"Released port {port} (total allocated: {len(self.allocated_ports)})")
        else:
            logger.warning(f"Attempted to release unallocated port: {port}")
    
    def is_port_allocated(self, port: int) -> bool:
        """
        Check if a port is currently allocated
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is allocated, False otherwise
        """
        return port in self.allocated_ports
    
    def get_allocated_count(self) -> int:
        """
        Get count of currently allocated ports
        
        Returns:
            Number of allocated ports
        """
        return len(self.allocated_ports)
    
    def get_available_count(self) -> int:
        """
        Get count of available ports
        
        Returns:
            Number of available ports
        """
        return self.max_ports - len(self.allocated_ports)
    
    def can_allocate(self) -> bool:
        """
        Check if a port can be allocated
        
        Returns:
            True if port allocation is possible, False otherwise
        """
        return len(self.allocated_ports) < self.max_ports
    
    def reset(self) -> None:
        """
        Reset all port allocations (use with caution)
        """
        count = len(self.allocated_ports)
        self.allocated_ports.clear()
        logger.warning(f"Reset all port allocations ({count} ports released)")
