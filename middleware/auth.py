"""
API Key Authentication Middleware
"""
import logging
from fastapi import Header, HTTPException, status
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


class AuthenticationError(HTTPException):
    """Custom exception for authentication failures"""
    
    def __init__(self, detail: str = "Invalid or missing API key"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from request header
    
    This dependency can be added to any endpoint that requires authentication.
    It checks the X-API-Key header against the configured API key.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The validated API key
        
    Raises:
        AuthenticationError: If API key is missing or invalid
    """
    # Skip authentication if not required
    if not settings.require_api_key:
        logger.debug("API key authentication is disabled")
        return "authentication_disabled"
    
    # Check if API key is provided
    if not x_api_key:
        logger.warning("Request missing API key")
        raise AuthenticationError("Missing API key. Please provide X-API-Key header")
    
    # Validate API key
    if x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
        raise AuthenticationError("Invalid API key")
    
    logger.debug("API key validated successfully")
    return x_api_key
