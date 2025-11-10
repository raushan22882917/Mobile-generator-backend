"""
Input Sanitization Utilities
Validates and sanitizes user inputs to prevent injection attacks
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


class SanitizationError(ValueError):
    """Raised when input fails sanitization checks"""
    pass


# Dangerous patterns that could indicate command injection attempts
DANGEROUS_PATTERNS = [
    r'[;&|`]',  # Shell command separators (removed $ as it's common in text)
    r'\$\(',  # Command substitution
    r'\.\.\/',  # Directory traversal (more specific pattern)
    r'<script',  # Script tags (case insensitive)
    r'javascript:',  # JavaScript protocol
    r'on\w+\s*=',  # Event handlers (onclick, onerror, etc.)
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]


def sanitize_prompt(prompt: str, max_length: int = 5000) -> str:
    """
    Sanitize user prompt to prevent injection attacks
    
    Validates that the prompt:
    - Is within length limits
    - Doesn't contain dangerous shell characters
    - Doesn't contain script injection attempts
    - Contains only printable characters
    
    Args:
        prompt: User-provided prompt text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized prompt string
        
    Raises:
        SanitizationError: If prompt fails validation
    """
    if not prompt:
        raise SanitizationError("Prompt cannot be empty")
    
    # Check length
    if len(prompt) > max_length:
        raise SanitizationError(f"Prompt exceeds maximum length of {max_length} characters")
    
    # Check for dangerous patterns
    for pattern in COMPILED_PATTERNS:
        if pattern.search(prompt):
            logger.warning(f"Dangerous pattern detected in prompt: {pattern.pattern}")
            raise SanitizationError(
                "Prompt contains potentially dangerous characters or patterns. "
                "Please use only alphanumeric characters and basic punctuation."
            )
    
    # Check for excessive special characters (potential obfuscation)
    # Allow common punctuation: . , ! ? ' " - : ( ) / @ # % & + =
    special_char_count = sum(1 for c in prompt if not c.isalnum() and not c.isspace() and c not in ".,!?'\"-:()/@#%&+=")
    if special_char_count > len(prompt) * 0.5:  # More than 50% unusual special characters
        logger.warning(f"Excessive special characters in prompt: {special_char_count}/{len(prompt)}")
        raise SanitizationError(
            "Prompt contains too many special characters. "
            "Please use natural language to describe your app."
        )
    
    # Strip leading/trailing whitespace
    sanitized = prompt.strip()
    
    # Normalize excessive whitespace but preserve newlines
    # Replace multiple spaces/tabs with single space, but keep newlines
    sanitized = re.sub(r'[ \t]+', ' ', sanitized)
    # Limit consecutive newlines to 2
    sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
    
    logger.debug(f"Prompt sanitized successfully (length: {len(sanitized)})")
    return sanitized


def sanitize_path(path: str, allowed_base_dirs: List[str] = None) -> str:
    """
    Sanitize file path to prevent directory traversal attacks
    
    Validates that the path:
    - Doesn't contain directory traversal sequences (..)
    - Doesn't contain absolute paths
    - Is within allowed base directories (if specified)
    - Doesn't contain shell special characters
    
    Args:
        path: File path to sanitize
        allowed_base_dirs: Optional list of allowed base directories
        
    Returns:
        Sanitized path string
        
    Raises:
        SanitizationError: If path fails validation
    """
    if not path:
        raise SanitizationError("Path cannot be empty")
    
    # Check for directory traversal
    if '..' in path:
        logger.warning(f"Directory traversal attempt detected: {path}")
        raise SanitizationError("Path contains directory traversal sequence")
    
    # Check for absolute paths (Unix and Windows)
    if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
        logger.warning(f"Absolute path detected: {path}")
        raise SanitizationError("Absolute paths are not allowed")
    
    # Check for shell special characters
    if re.search(r'[;&|`$<>]', path):
        logger.warning(f"Shell special characters in path: {path}")
        raise SanitizationError("Path contains invalid characters")
    
    # Normalize path separators
    sanitized = path.replace('\\', '/')
    
    # Remove leading/trailing slashes
    sanitized = sanitized.strip('/')
    
    # Check if path is within allowed directories
    if allowed_base_dirs:
        import os
        normalized_path = os.path.normpath(sanitized)
        is_allowed = any(
            normalized_path.startswith(os.path.normpath(base_dir))
            for base_dir in allowed_base_dirs
        )
        if not is_allowed:
            logger.warning(f"Path outside allowed directories: {path}")
            raise SanitizationError("Path is outside allowed directories")
    
    logger.debug(f"Path sanitized successfully: {sanitized}")
    return sanitized


def sanitize_command_arg(arg: str) -> str:
    """
    Sanitize command line argument to prevent command injection
    
    This is used when constructing shell commands to ensure arguments
    don't contain shell metacharacters that could be exploited.
    
    Args:
        arg: Command line argument to sanitize
        
    Returns:
        Sanitized argument string
        
    Raises:
        SanitizationError: If argument fails validation
    """
    if not arg:
        raise SanitizationError("Command argument cannot be empty")
    
    # Check for shell metacharacters
    dangerous_chars = r'[;&|`$<>(){}[\]!*?~]'
    if re.search(dangerous_chars, arg):
        logger.warning(f"Dangerous characters in command argument: {arg}")
        raise SanitizationError(
            "Command argument contains shell metacharacters. "
            "Only alphanumeric characters, hyphens, and underscores are allowed."
        )
    
    # Check for quotes (can be used to break out of quoted strings)
    if '"' in arg or "'" in arg:
        logger.warning(f"Quotes in command argument: {arg}")
        raise SanitizationError("Command argument cannot contain quotes")
    
    # Ensure only safe characters (alphanumeric, hyphen, underscore, dot, slash)
    if not re.match(r'^[a-zA-Z0-9._/-]+$', arg):
        logger.warning(f"Invalid characters in command argument: {arg}")
        raise SanitizationError(
            "Command argument contains invalid characters. "
            "Only alphanumeric characters, hyphens, underscores, dots, and slashes are allowed."
        )
    
    logger.debug(f"Command argument sanitized successfully: {arg}")
    return arg


def validate_project_id(project_id: str) -> str:
    """
    Validate project ID format
    
    Project IDs should be UUIDs or similar safe identifiers.
    
    Args:
        project_id: Project ID to validate
        
    Returns:
        Validated project ID
        
    Raises:
        SanitizationError: If project ID is invalid
    """
    if not project_id:
        raise SanitizationError("Project ID cannot be empty")
    
    # Check length (UUIDs are 36 characters with hyphens, 32 without)
    if len(project_id) < 8 or len(project_id) > 36:
        raise SanitizationError("Invalid project ID length")
    
    # Check format (alphanumeric and hyphens only)
    if not re.match(r'^[a-zA-Z0-9-]+$', project_id):
        logger.warning(f"Invalid project ID format: {project_id}")
        raise SanitizationError("Project ID contains invalid characters")
    
    return project_id


def sanitize_user_id(user_id: str, max_length: int = 100) -> str:
    """
    Sanitize user ID
    
    Args:
        user_id: User identifier to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized user ID
        
    Raises:
        SanitizationError: If user ID is invalid
    """
    if not user_id:
        return "anonymous"
    
    # Check length
    if len(user_id) > max_length:
        raise SanitizationError(f"User ID exceeds maximum length of {max_length}")
    
    # Remove any dangerous characters
    sanitized = re.sub(r'[^a-zA-Z0-9_@.-]', '', user_id)
    
    if not sanitized:
        return "anonymous"
    
    return sanitized
