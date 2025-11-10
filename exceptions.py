"""
Custom Exception Classes
Centralized error handling with categorization and user-friendly messages
"""


class AppBuilderError(Exception):
    """
    Base exception for all AI Expo App Builder errors
    
    All custom exceptions should inherit from this base class.
    Provides common functionality for error categorization and messaging.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        """
        Initialize AppBuilderError
        
        Args:
            message: Error message describing what went wrong
            suggestion: Optional user-friendly suggestion for resolving the error
        """
        self.message = message
        self.suggestion = suggestion or "Please try again or contact support if the problem persists"
        super().__init__(self.message)
    
    def get_error_type(self) -> str:
        """
        Get the error type identifier
        
        Returns:
            String identifier for the error type
        """
        # Convert CamelCase to SNAKE_CASE
        import re
        name = self.__class__.__name__.replace("Error", "")
        # Insert underscore before uppercase letters
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.upper() + "_ERROR"
    
    def to_dict(self) -> dict:
        """
        Convert error to dictionary for API responses
        
        Returns:
            Dictionary with error details
        """
        return {
            "error": self.get_error_type(),
            "message": self.message,
            "suggestion": self.suggestion
        }


# AI Generation Errors
class AIGenerationError(AppBuilderError):
    """
    Raised when AI code generation fails
    
    This includes OpenAI API errors, timeouts, and invalid responses.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "Try rephrasing your prompt or simplifying the requirements"
        super().__init__(message, suggestion)


class CodeValidationError(AIGenerationError):
    """
    Raised when generated code fails validation
    
    This occurs when the AI generates code that doesn't meet
    the required structure or quality standards.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "Try providing more specific requirements in your prompt"
        super().__init__(message, suggestion)


# Dependency Installation Errors
class DependencyInstallError(AppBuilderError):
    """
    Raised when npm install or dependency installation fails
    
    This includes network errors, package conflicts, and installation timeouts.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "This is usually temporary. Please try again in a few moments"
        super().__init__(message, suggestion)


# Server Startup Errors
class ServerStartError(AppBuilderError):
    """
    Raised when Expo development server fails to start
    
    This includes port conflicts, configuration errors, and startup timeouts.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "The server failed to start. Please try generating the app again"
        super().__init__(message, suggestion)


# Tunnel Creation Errors
class TunnelCreationError(AppBuilderError):
    """
    Raised when public tunnel creation fails
    
    This includes ngrok errors, authentication failures, and connection issues.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "Unable to create preview tunnel. Please try again"
        super().__init__(message, suggestion)


# Resource Limit Errors
class ResourceLimitError(AppBuilderError):
    """
    Raised when system resource limits are exceeded
    
    This includes CPU, memory, disk space, and concurrent project limits.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "System resources are currently limited. Please try again in a few minutes"
        super().__init__(message, suggestion)


class MaxProjectsError(ResourceLimitError):
    """
    Raised when maximum concurrent projects limit is reached
    """
    
    def __init__(self, max_projects: int, suggestion: str = None):
        message = f"Maximum concurrent projects limit reached ({max_projects})"
        if suggestion is None:
            suggestion = "Please wait for other projects to complete or try again later"
        super().__init__(message, suggestion)


class DiskSpaceError(ResourceLimitError):
    """
    Raised when disk space is insufficient
    """
    
    def __init__(self, available_percent: float, suggestion: str = None):
        message = f"Insufficient disk space (only {available_percent:.1f}% available)"
        if suggestion is None:
            suggestion = "System is cleaning up old projects. Please try again in a few minutes"
        super().__init__(message, suggestion)


class MemoryLimitError(ResourceLimitError):
    """
    Raised when memory usage is too high
    """
    
    def __init__(self, memory_percent: float, suggestion: str = None):
        message = f"System memory usage too high ({memory_percent:.1f}%)"
        if suggestion is None:
            suggestion = "System is under heavy load. Please try again in a few minutes"
        super().__init__(message, suggestion)


# Command Execution Errors
class CommandExecutionError(AppBuilderError):
    """
    Raised when shell command execution fails
    
    This includes subprocess errors, timeouts, and non-zero exit codes.
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "Command execution failed. Please try again"
        super().__init__(message, suggestion)


class CommandTimeoutError(CommandExecutionError):
    """
    Raised when command execution times out
    """
    
    def __init__(self, command: str, timeout: int, suggestion: str = None):
        message = f"Command timed out after {timeout} seconds: {command}"
        if suggestion is None:
            suggestion = "The operation took too long. Please try with a simpler app or try again"
        super().__init__(message, suggestion)


# Project Management Errors
class ProjectNotFoundError(AppBuilderError):
    """
    Raised when a requested project doesn't exist
    """
    
    def __init__(self, project_id: str, suggestion: str = None):
        message = f"Project not found: {project_id}"
        if suggestion is None:
            suggestion = "The project may have been cleaned up or never existed"
        super().__init__(message, suggestion)


class ProjectNotReadyError(AppBuilderError):
    """
    Raised when attempting operations on a project that isn't ready
    """
    
    def __init__(self, project_id: str, status: str, suggestion: str = None):
        message = f"Project is not ready (status: {status})"
        if suggestion is None:
            suggestion = "Wait for the project to complete generation before performing this operation"
        super().__init__(message, suggestion)


# Code Generation Errors (legacy compatibility)
class CodeGenerationError(AIGenerationError):
    """
    Legacy alias for AIGenerationError
    Maintained for backward compatibility with existing code
    """
    pass


# Validation Errors
class ValidationError(AppBuilderError):
    """
    Raised when request validation fails
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "Please check your request parameters and try again"
        super().__init__(message, suggestion)


# Archive/Download Errors
class ArchiveCreationError(AppBuilderError):
    """
    Raised when project archive creation fails
    """
    
    def __init__(self, message: str, suggestion: str = None):
        if suggestion is None:
            suggestion = "Failed to create project archive. Please try again"
        super().__init__(message, suggestion)


# Helper function to categorize errors
def categorize_error(error: Exception) -> str:
    """
    Categorize an error into a user-friendly category
    
    Args:
        error: Exception to categorize
        
    Returns:
        Category string (AI, dependency, server, tunnel, resource, or unknown)
    """
    if isinstance(error, AIGenerationError):
        return "AI"
    elif isinstance(error, DependencyInstallError):
        return "dependency"
    elif isinstance(error, ServerStartError):
        return "server"
    elif isinstance(error, TunnelCreationError):
        return "tunnel"
    elif isinstance(error, ResourceLimitError):
        return "resource"
    elif isinstance(error, CommandExecutionError):
        return "command"
    elif isinstance(error, AppBuilderError):
        return "application"
    else:
        return "unknown"


# Helper function to get error response
def get_error_response(error: Exception, project_id: str = None) -> dict:
    """
    Convert any exception to a standardized error response
    
    Args:
        error: Exception to convert
        project_id: Optional project ID associated with the error
        
    Returns:
        Dictionary with error details for API response
    """
    from datetime import datetime
    
    if isinstance(error, AppBuilderError):
        response = error.to_dict()
    else:
        # Handle unexpected errors
        response = {
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(error) if str(error) else "An unexpected error occurred",
            "suggestion": "Please try again later or contact support if the problem persists"
        }
    
    # Add optional fields
    if project_id:
        response["project_id"] = project_id
    
    response["timestamp"] = datetime.now().isoformat()
    response["category"] = categorize_error(error)
    
    return response
