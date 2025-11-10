"""
Rate Limiting Middleware
Implements token bucket algorithm for rate limiting requests
"""
import logging
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded"""
    
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again in {retry_after} seconds",
            headers={"Retry-After": str(retry_after)}
        )


class TokenBucket:
    """
    Token bucket implementation for rate limiting
    
    Each user gets a bucket with a maximum capacity of tokens.
    Tokens are consumed on each request and refilled at a constant rate.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> Tuple[bool, int]:
        """
        Try to consume tokens from the bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            Tuple of (success, retry_after_seconds)
        """
        # Refill tokens based on time elapsed
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, 0
        else:
            # Calculate how long until we have enough tokens
            tokens_needed = tokens - self.tokens
            retry_after = int(tokens_needed / self.refill_rate) + 1
            return False, retry_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests
    
    Implements per-user rate limiting using token bucket algorithm.
    Rate limit: 10 requests per minute per user.
    """
    
    def __init__(self, app, requests_per_minute: int = 10):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per user
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(requests_per_minute, self.refill_rate)
        )
        logger.info(f"Rate limiting enabled: {requests_per_minute} requests per minute")
    
    def get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client
        
        Uses API key if available, otherwise falls back to IP address.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client identifier string
        """
        # Try to get API key from header
        api_key = request.headers.get("x-api-key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with rate limiting
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # Only apply rate limiting to /generate endpoint
        if not request.url.path.startswith("/generate"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self.get_client_identifier(request)
        
        # Get or create token bucket for this client
        bucket = self.buckets[client_id]
        
        # Try to consume a token
        allowed, retry_after = bucket.consume(1)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id}. "
                f"Retry after {retry_after} seconds"
            )
            raise RateLimitExceeded(retry_after)
        
        logger.debug(f"Request allowed for {client_id}. Tokens remaining: {bucket.tokens:.2f}")
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response
    
    def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """
        Clean up old token buckets to prevent memory leaks
        
        This should be called periodically (e.g., every hour) to remove
        buckets for clients that haven't made requests recently.
        
        Args:
            max_age_seconds: Maximum age of bucket before cleanup
        """
        now = time.time()
        old_clients = [
            client_id
            for client_id, bucket in self.buckets.items()
            if now - bucket.last_refill > max_age_seconds
        ]
        
        for client_id in old_clients:
            del self.buckets[client_id]
        
        if old_clients:
            logger.info(f"Cleaned up {len(old_clients)} old rate limit buckets")
