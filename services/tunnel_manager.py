"""
Tunnel Manager Service
Handles creation and management of public tunnels using ngrok
"""
import asyncio
import logging
from typing import Dict, Optional
from pyngrok import ngrok, conf
from pyngrok.exception import PyngrokError

from exceptions import TunnelCreationError
from utils.retry import retry, RetryConfig

logger = logging.getLogger(__name__)


class TunnelManager:
    """Service for managing ngrok tunnels to expose local Expo servers"""
    
    def __init__(
        self,
        auth_token: str,
        tunnel_type: str = "ngrok",
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize TunnelManager
        
        Args:
            auth_token: Ngrok authentication token
            tunnel_type: Type of tunnel service (default: "ngrok")
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay in seconds between retries (default: 5)
        """
        self.auth_token = auth_token
        self.tunnel_type = tunnel_type
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.active_tunnels: Dict[str, ngrok.NgrokTunnel] = {}
        
        # Configure ngrok with auth token
        conf.get_default().auth_token = auth_token
        
        logger.info(
            f"TunnelManager initialized with tunnel_type: {tunnel_type}, "
            f"max_retries: {max_retries}"
        )
    
    @retry(max_attempts=3, delay=5.0, backoff=1.0, exceptions=(Exception,))
    async def create_tunnel(self, port: int, project_id: str) -> str:
        """
        Create public tunnel and return URL with retry logic
        
        Args:
            port: Local port to expose
            project_id: Project identifier for tracking
            
        Returns:
            Public HTTPS URL for the tunnel
            
        Raises:
            TunnelCreationError: If tunnel creation fails after all retries
        """
        logger.info(f"Creating tunnel for project {project_id} on port {port}")
        
        try:
            # Create ngrok tunnel
            tunnel = await self._start_ngrok(port)
            
            # Store active tunnel
            self.active_tunnels[project_id] = tunnel
            
            # Get public URL
            public_url = tunnel.public_url
            
            logger.info(
                f"Tunnel created successfully for project {project_id}: {public_url}"
            )
            
            return public_url
            
        except PyngrokError as e:
            error_msg = str(e)
            logger.error(f"Pyngrok error creating tunnel: {error_msg}")
            
            # Provide helpful error message for authentication failures
            if "authentication failed" in error_msg.lower() or "ERR_NGROK_107" in error_msg:
                suggestion = (
                    "Your ngrok authtoken is invalid. Please:\n"
                    "1. Visit https://dashboard.ngrok.com/get-started/your-authtoken\n"
                    "2. Copy your valid authtoken\n"
                    "3. Update NGROK_AUTH_TOKEN in your .env file\n"
                    "4. Restart the server"
                )
                raise TunnelCreationError(
                    f"Failed to create tunnel: {error_msg}",
                    suggestion=suggestion
                )
            
            raise TunnelCreationError(
                f"Failed to create tunnel: {error_msg}"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating tunnel: {str(e)}")
            raise TunnelCreationError(
                f"Failed to create tunnel: {str(e)}"
            )
    
    async def _start_ngrok(self, port: int) -> ngrok.NgrokTunnel:
        """
        Start ngrok tunnel using pyngrok library
        
        Args:
            port: Local port to expose
            
        Returns:
            NgrokTunnel object
            
        Raises:
            PyngrokError: If ngrok fails to start
        """
        try:
            # Run ngrok.connect in executor to avoid blocking
            loop = asyncio.get_event_loop()
            tunnel = await loop.run_in_executor(
                None,
                lambda: ngrok.connect(port, bind_tls=True)
            )
            
            logger.debug(f"Ngrok tunnel started on port {port}: {tunnel.public_url}")
            return tunnel
            
        except PyngrokError as e:
            logger.error(f"Pyngrok error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error starting ngrok: {str(e)}")
            raise
    
    async def close_tunnel(self, project_id: str) -> None:
        """
        Close tunnel and free resources
        
        Args:
            project_id: Project identifier
        """
        tunnel = self.active_tunnels.get(project_id)
        
        if not tunnel:
            logger.warning(
                f"Attempted to close non-existent tunnel for project {project_id}"
            )
            return
        
        try:
            # Close the tunnel
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: ngrok.disconnect(tunnel.public_url)
            )
            
            # Remove from active tunnels
            del self.active_tunnels[project_id]
            
            logger.info(f"Tunnel closed for project {project_id}")
            
        except Exception as e:
            logger.error(
                f"Error closing tunnel for project {project_id}: {str(e)}"
            )
            # Still remove from tracking even if close failed
            if project_id in self.active_tunnels:
                del self.active_tunnels[project_id]
    
    async def cleanup_orphaned_tunnels(self) -> int:
        """
        Cleanup orphaned tunnels that are no longer tracked
        
        Returns:
            Number of tunnels cleaned up
        """
        try:
            # Get all active ngrok tunnels
            loop = asyncio.get_event_loop()
            tunnels = await loop.run_in_executor(
                None,
                ngrok.get_tunnels
            )
            
            cleanup_count = 0
            
            # Check each tunnel
            for tunnel in tunnels:
                # Find if this tunnel is tracked
                is_tracked = any(
                    t.public_url == tunnel.public_url
                    for t in self.active_tunnels.values()
                )
                
                if not is_tracked:
                    # This is an orphaned tunnel, close it
                    try:
                        await loop.run_in_executor(
                            None,
                            lambda: ngrok.disconnect(tunnel.public_url)
                        )
                        cleanup_count += 1
                        logger.info(f"Cleaned up orphaned tunnel: {tunnel.public_url}")
                    except Exception as e:
                        logger.error(
                            f"Failed to cleanup orphaned tunnel {tunnel.public_url}: {str(e)}"
                        )
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} orphaned tunnels")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during orphaned tunnel cleanup: {str(e)}")
            return 0
    
    def get_tunnel_url(self, project_id: str) -> Optional[str]:
        """
        Get tunnel URL for a project
        
        Args:
            project_id: Project identifier
            
        Returns:
            Public URL or None if tunnel doesn't exist
        """
        tunnel = self.active_tunnels.get(project_id)
        return tunnel.public_url if tunnel else None
    
    def get_active_tunnel_count(self) -> int:
        """
        Get count of active tunnels
        
        Returns:
            Number of active tunnels
        """
        return len(self.active_tunnels)
    
    def list_active_tunnels(self) -> Dict[str, str]:
        """
        Get all active tunnels
        
        Returns:
            Dictionary mapping project IDs to public URLs
        """
        return {
            project_id: tunnel.public_url
            for project_id, tunnel in self.active_tunnels.items()
        }
    
    async def close_all_tunnels(self) -> None:
        """
        Close all active tunnels
        """
        project_ids = list(self.active_tunnels.keys())
        
        for project_id in project_ids:
            await self.close_tunnel(project_id)
        
        logger.info(f"Closed all {len(project_ids)} active tunnels")
