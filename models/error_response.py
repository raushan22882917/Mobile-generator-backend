"""
Error Response Models
Standardized error response formatting with user-friendly messages
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ErrorCategory(str, Enum):
    """Error category enumeration"""
    AI = "AI"
    DEPENDENCY = "dependency"
    SERVER = "server"
    TUNNEL = "tunnel"
    RESOURCE = "resource"
    COMMAND = "command"
    APPLICATION = "application"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class ErrorResponse(BaseModel):
    """
    Standardized error response model
    
    Provides consistent error formatting across all API endpoints
    with user-friendly messages and troubleshooting suggestions.
    """
    
    error: str = Field(
        ...,
        description="Error type identifier (e.g., AI_GENERATION_ERROR)"
    )
    
    message: str = Field(
        ...,
        description="Detailed error message describing what went wrong"
    )
    
    suggestion: str = Field(
        ...,
        description="User-friendly suggestion for resolving the error"
    )
    
    category: ErrorCategory = Field(
        default=ErrorCategory.UNKNOWN,
        description="Error category for grouping and filtering"
    )
    
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID associated with the error (if applicable)"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO 8601 timestamp when the error occurred"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details (for debugging)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "AI_GENERATION_ERROR",
                "message": "Failed to generate code: OpenAI API timeout",
                "suggestion": "Try rephrasing your prompt or simplifying the requirements",
                "category": "AI",
                "project_id": "abc123",
                "timestamp": "2024-01-15T10:30:00.000Z",
                "details": None
            }
        }


# Predefined error messages and suggestions
ERROR_MESSAGES = {
    # AI Generation Errors
    "AI_GENERATION_ERROR": {
        "message": "Failed to generate application code",
        "suggestion": "Try rephrasing your prompt or simplifying the requirements",
        "category": ErrorCategory.AI
    },
    "CODE_VALIDATION_ERROR": {
        "message": "Generated code failed validation",
        "suggestion": "Try providing more specific requirements in your prompt",
        "category": ErrorCategory.AI
    },
    "AI_TIMEOUT_ERROR": {
        "message": "Code generation timed out",
        "suggestion": "Try with a simpler app description or try again",
        "category": ErrorCategory.AI
    },
    
    # Dependency Installation Errors
    "DEPENDENCY_INSTALL_ERROR": {
        "message": "Failed to install project dependencies",
        "suggestion": "This is usually temporary. Please try again in a few moments",
        "category": ErrorCategory.DEPENDENCY
    },
    "NPM_INSTALL_ERROR": {
        "message": "npm install failed",
        "suggestion": "Check your internet connection and try again",
        "category": ErrorCategory.DEPENDENCY
    },
    
    # Server Startup Errors
    "SERVER_START_ERROR": {
        "message": "Failed to start Expo development server",
        "suggestion": "The server failed to start. Please try generating the app again",
        "category": ErrorCategory.SERVER
    },
    "PORT_CONFLICT_ERROR": {
        "message": "Port is already in use",
        "suggestion": "Please try again - a new port will be allocated",
        "category": ErrorCategory.SERVER
    },
    
    # Tunnel Creation Errors
    "TUNNEL_CREATION_ERROR": {
        "message": "Failed to create public preview tunnel",
        "suggestion": "Unable to create preview tunnel. Please try again",
        "category": ErrorCategory.TUNNEL
    },
    "NGROK_AUTH_ERROR": {
        "message": "Ngrok authentication failed",
        "suggestion": "Tunnel service authentication failed. Please contact support",
        "category": ErrorCategory.TUNNEL
    },
    
    # Resource Limit Errors
    "RESOURCE_LIMIT_ERROR": {
        "message": "System resource limits exceeded",
        "suggestion": "System resources are currently limited. Please try again in a few minutes",
        "category": ErrorCategory.RESOURCE
    },
    "MAX_PROJECTS_ERROR": {
        "message": "Maximum concurrent projects limit reached",
        "suggestion": "Please wait for other projects to complete or try again later",
        "category": ErrorCategory.RESOURCE
    },
    "DISK_SPACE_ERROR": {
        "message": "Insufficient disk space",
        "suggestion": "System is cleaning up old projects. Please try again in a few minutes",
        "category": ErrorCategory.RESOURCE
    },
    "MEMORY_LIMIT_ERROR": {
        "message": "System memory usage too high",
        "suggestion": "System is under heavy load. Please try again in a few minutes",
        "category": ErrorCategory.RESOURCE
    },
    
    # Command Execution Errors
    "COMMAND_EXECUTION_ERROR": {
        "message": "Command execution failed",
        "suggestion": "Command execution failed. Please try again",
        "category": ErrorCategory.COMMAND
    },
    "COMMAND_TIMEOUT_ERROR": {
        "message": "Command execution timed out",
        "suggestion": "The operation took too long. Please try with a simpler app or try again",
        "category": ErrorCategory.COMMAND
    },
    
    # Project Management Errors
    "PROJECT_NOT_FOUND": {
        "message": "Project not found",
        "suggestion": "The project may have been cleaned up or never existed",
        "category": ErrorCategory.APPLICATION
    },
    "PROJECT_NOT_READY": {
        "message": "Project is not ready",
        "suggestion": "Wait for the project to complete generation before performing this operation",
        "category": ErrorCategory.APPLICATION
    },
    
    # Validation Errors
    "VALIDATION_ERROR": {
        "message": "Invalid request data",
        "suggestion": "Please check your request parameters and try again",
        "category": ErrorCategory.VALIDATION
    },
    "PROMPT_TOO_SHORT": {
        "message": "Prompt is too short",
        "suggestion": "Please provide at least 10 characters describing your app",
        "category": ErrorCategory.VALIDATION
    },
    "PROMPT_TOO_LONG": {
        "message": "Prompt is too long",
        "suggestion": "Please keep your app description under 5000 characters",
        "category": ErrorCategory.VALIDATION
    },
    
    # Archive/Download Errors
    "ARCHIVE_CREATION_ERROR": {
        "message": "Failed to create project archive",
        "suggestion": "Failed to create project archive. Please try again",
        "category": ErrorCategory.APPLICATION
    },
    
    # Generic Errors
    "INTERNAL_SERVER_ERROR": {
        "message": "An unexpected error occurred",
        "suggestion": "Please try again later or contact support if the problem persists",
        "category": ErrorCategory.UNKNOWN
    }
}


def create_error_response(
    error_type: str,
    message: Optional[str] = None,
    suggestion: Optional[str] = None,
    category: Optional[ErrorCategory] = None,
    project_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """
    Create a standardized error response
    
    Args:
        error_type: Error type identifier (e.g., "AI_GENERATION_ERROR")
        message: Optional custom error message (uses default if None)
        suggestion: Optional custom suggestion (uses default if None)
        category: Optional error category (inferred if None)
        project_id: Optional project ID
        details: Optional additional details
        
    Returns:
        ErrorResponse instance
    """
    # Get default values from ERROR_MESSAGES if available
    defaults = ERROR_MESSAGES.get(error_type, {})
    
    # Use provided values or fall back to defaults
    final_message = message or defaults.get("message", "An error occurred")
    final_suggestion = suggestion or defaults.get(
        "suggestion",
        "Please try again or contact support if the problem persists"
    )
    final_category = category or defaults.get("category", ErrorCategory.UNKNOWN)
    
    return ErrorResponse(
        error=error_type,
        message=final_message,
        suggestion=final_suggestion,
        category=final_category,
        project_id=project_id,
        details=details
    )


def error_from_exception(
    exception: Exception,
    project_id: Optional[str] = None,
    include_details: bool = False
) -> ErrorResponse:
    """
    Create error response from an exception
    
    Args:
        exception: Exception to convert
        project_id: Optional project ID
        include_details: Whether to include exception details (for debugging)
        
    Returns:
        ErrorResponse instance
    """
    from exceptions import (
        AppBuilderError,
        AIGenerationError,
        DependencyInstallError,
        ServerStartError,
        TunnelCreationError,
        ResourceLimitError,
        CommandExecutionError,
        categorize_error
    )
    
    # Determine error type and get details
    if isinstance(exception, AppBuilderError):
        error_type = exception.get_error_type()
        message = exception.message
        suggestion = exception.suggestion
        category_str = categorize_error(exception)
    else:
        error_type = "INTERNAL_SERVER_ERROR"
        message = str(exception) if str(exception) else "An unexpected error occurred"
        suggestion = "Please try again later or contact support if the problem persists"
        category_str = "unknown"
    
    # Convert category string to enum
    try:
        category = ErrorCategory(category_str)
    except ValueError:
        category = ErrorCategory.UNKNOWN
    
    # Include exception details if requested
    details = None
    if include_details:
        details = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception)
        }
    
    return ErrorResponse(
        error=error_type,
        message=message,
        suggestion=suggestion,
        category=category,
        project_id=project_id,
        details=details
    )


def get_troubleshooting_tips(error_type: str) -> list[str]:
    """
    Get troubleshooting tips for a specific error type
    
    Args:
        error_type: Error type identifier
        
    Returns:
        List of troubleshooting tips
    """
    tips = {
        "AI_GENERATION_ERROR": [
            "Try rephrasing your prompt to be more specific",
            "Simplify your requirements and add features incrementally",
            "Check if the OpenAI service is experiencing issues",
            "Try again in a few moments"
        ],
        "DEPENDENCY_INSTALL_ERROR": [
            "Check your internet connection",
            "Try again - npm registry might be temporarily unavailable",
            "Simplify your app to use fewer dependencies"
        ],
        "TUNNEL_CREATION_ERROR": [
            "Try again - tunnel service might be temporarily unavailable",
            "Check if ngrok service is operational",
            "Contact support if the problem persists"
        ],
        "RESOURCE_LIMIT_ERROR": [
            "Wait a few minutes for resources to free up",
            "Try during off-peak hours",
            "Contact support to increase your resource limits"
        ],
        "COMMAND_TIMEOUT_ERROR": [
            "Try with a simpler app description",
            "Check your internet connection for dependency downloads",
            "Try again - the system might be under heavy load"
        ]
    }
    
    return tips.get(error_type, [
        "Try again in a few moments",
        "Contact support if the problem persists"
    ])
