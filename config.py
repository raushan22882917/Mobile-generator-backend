"""
Configuration management using Pydantic Settings
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys (required)
    openai_api_key: str = Field(..., min_length=1, description="OpenAI API key for code generation")
    ngrok_auth_token: str = Field(..., min_length=1, description="Ngrok authentication token for tunneling")
    
    # Optional API Keys
    gemini_api_key: str = Field(default="", description="Google Gemini API key for fallback when OpenAI quota exceeded (optional)")
    
    # API Authentication
    api_key: str = Field(default="", description="API key for authenticating requests to /generate endpoint")
    require_api_key: bool = Field(default=False, description="Whether to require API key authentication")
    
    # Google Cloud (required for production)
    google_cloud_project: str = Field(
        default="",
        description="Google Cloud Project ID (required for production)"
    )
    google_cloud_bucket: str = Field(
        default="",
        description="Google Cloud Storage bucket for project storage (required for production)"
    )
    google_application_credentials: str = Field(
        default="",
        description="Path to Google Cloud credentials JSON file (optional - uses environment variable or default credentials)"
    )
    
    # Firebase Authentication
    firebase_credentials_path: str = Field(
        default="",
        description="Path to Firebase Admin SDK credentials JSON file (required for Firebase authentication)"
    )
    firebase_api_key: str = Field(
        default="AIzaSyAN5hfhAjpLOy7I9nPZiZeolFtCUT7PQ3g",
        description="Firebase Web API Key (required for password authentication via REST API). Get from Firebase Console > Project Settings > General > Web API Key"
    )
    
    # Application Settings
    max_concurrent_projects: int = 10
    project_timeout_minutes: int = 30
    base_port: int = 19006
    code_generation_timeout: int = 900  # 15 minutes in seconds
    
    # Resource Limits
    max_cpu_percent: float = 90.0
    max_memory_percent: float = 95.0
    min_disk_percent: float = 5.0
    
    # Paths
    projects_base_dir: str = Field(
        default="/tmp/projects",
        description="Base directory for temporary project files (cleaned up after upload to Cloud Storage)"
    )
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key is not empty."""
        if not v or not v.strip():
            raise ValueError("OpenAI API key is required and cannot be empty")
        return v.strip()
    
    @field_validator("ngrok_auth_token")
    @classmethod
    def validate_ngrok_token(cls, v: str) -> str:
        """Validate ngrok auth token is not empty."""
        if not v or not v.strip():
            raise ValueError("Ngrok auth token is required and cannot be empty")
        return v.strip()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
