"""
Retry Utility
Provides retry decorator with exponential backoff for handling transient failures
"""
import asyncio
import logging
from typing import Callable, TypeVar, Any, Type, Tuple, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def with_retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> T:
    """
    Execute async function with exponential backoff retry
    
    Args:
        func: Async function to execute
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay in seconds between retries (default: 1.0)
        backoff: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
        on_retry: Optional callback function called on each retry with (exception, attempt)
        
    Returns:
        Result from successful function execution
        
    Raises:
        Last exception if all attempts fail
        
    Example:
        result = await with_retry(
            lambda: some_async_function(),
            max_attempts=3,
            delay=2.0,
            backoff=2.0
        )
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(f"Attempt {attempt}/{max_attempts}")
            result = await func()
            
            if attempt > 1:
                logger.info(f"Operation succeeded on attempt {attempt}/{max_attempts}")
            
            return result
            
        except exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                logger.error(
                    f"Operation failed after {max_attempts} attempts: {str(e)}"
                )
                raise
            
            logger.warning(
                f"Attempt {attempt}/{max_attempts} failed: {str(e)}. "
                f"Retrying in {current_delay:.1f}s..."
            )
            
            # Call retry callback if provided
            if on_retry:
                try:
                    on_retry(e, attempt)
                except Exception as callback_error:
                    logger.warning(f"Retry callback error: {callback_error}")
            
            # Wait before next attempt
            await asyncio.sleep(current_delay)
            
            # Increase delay for next attempt (exponential backoff)
            current_delay *= backoff
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected error in retry logic")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for async functions to add retry logic with exponential backoff
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay in seconds between retries (default: 1.0)
        backoff: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
        on_retry: Optional callback function called on each retry with (exception, attempt)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry(max_attempts=3, delay=2.0, backoff=2.0)
        async def create_tunnel(port: int):
            # Function that might fail transiently
            return await ngrok.connect(port)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await with_retry(
                func=lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions,
                on_retry=on_retry
            )
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for synchronous functions to add retry logic with exponential backoff
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay in seconds between retries (default: 1.0)
        backoff: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
        on_retry: Optional callback function called on each retry with (exception, attempt)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_sync(max_attempts=3, delay=1.0)
        def read_file(path: str):
            # Function that might fail transiently
            return open(path).read()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            import time
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"Attempt {attempt}/{max_attempts}")
                    result = func(*args, **kwargs)
                    
                    if attempt > 1:
                        logger.info(f"Operation succeeded on attempt {attempt}/{max_attempts}")
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Operation failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {str(e)}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.warning(f"Retry callback error: {callback_error}")
                    
                    # Wait before next attempt
                    time.sleep(current_delay)
                    
                    # Increase delay for next attempt (exponential backoff)
                    current_delay *= backoff
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected error in retry logic")
        
        return wrapper
    return decorator


class RetryConfig:
    """
    Configuration class for retry behavior
    
    Provides predefined retry configurations for common scenarios.
    """
    
    # Quick retries for fast operations (network requests, API calls)
    QUICK = {
        'max_attempts': 3,
        'delay': 1.0,
        'backoff': 2.0
    }
    
    # Standard retries for normal operations
    STANDARD = {
        'max_attempts': 3,
        'delay': 2.0,
        'backoff': 2.0
    }
    
    # Slow retries for heavy operations (tunnel creation, server startup)
    SLOW = {
        'max_attempts': 3,
        'delay': 5.0,
        'backoff': 2.0
    }
    
    # Aggressive retries for critical operations
    AGGRESSIVE = {
        'max_attempts': 5,
        'delay': 1.0,
        'backoff': 1.5
    }
    
    # Conservative retries for expensive operations
    CONSERVATIVE = {
        'max_attempts': 2,
        'delay': 3.0,
        'backoff': 2.0
    }


# Convenience functions for common retry patterns
async def retry_tunnel_creation(func: Callable[..., T]) -> T:
    """
    Retry tunnel creation with appropriate settings
    
    Args:
        func: Async function to execute
        
    Returns:
        Result from successful execution
    """
    return await with_retry(
        func=func,
        **RetryConfig.SLOW
    )


async def retry_command_execution(func: Callable[..., T]) -> T:
    """
    Retry command execution with appropriate settings
    
    Args:
        func: Async function to execute
        
    Returns:
        Result from successful execution
    """
    return await with_retry(
        func=func,
        **RetryConfig.STANDARD
    )


async def retry_api_call(func: Callable[..., T]) -> T:
    """
    Retry API call with appropriate settings
    
    Args:
        func: Async function to execute
        
    Returns:
        Result from successful execution
    """
    return await with_retry(
        func=func,
        **RetryConfig.QUICK
    )
