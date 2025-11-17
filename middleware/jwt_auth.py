"""
JWT Authentication Middleware
"""
import logging
from fastapi import Header, HTTPException, status, Depends
from typing import Optional

from services.auth_service import AuthService
from models.user import User

logger = logging.getLogger(__name__)

# Global auth service instance (will be initialized in lifespan)
auth_service: Optional[AuthService] = None


def set_auth_service(service: AuthService) -> None:
    """Set the global auth service instance"""
    global auth_service
    auth_service = service


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Get current authenticated user from JWT token
    
    This dependency can be added to any endpoint that requires authentication.
    It extracts the JWT token from the Authorization header and validates it.
    
    Args:
        authorization: Authorization header (format: "Bearer <token>")
        
    Returns:
        Authenticated User instance
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized"
        )
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify token and get user
    user = auth_service.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    
    This is useful for endpoints that work both with and without authentication.
    
    Args:
        authorization: Authorization header
        
    Returns:
        User instance if authenticated, None otherwise
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None

