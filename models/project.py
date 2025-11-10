"""
Data models for projects, code generation, and system metrics.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ProjectStatus(Enum):
    """Status of a project during its lifecycle."""
    INITIALIZING = "initializing"
    GENERATING_CODE = "generating_code"
    INSTALLING_DEPS = "installing_deps"
    STARTING_SERVER = "starting_server"
    CREATING_TUNNEL = "creating_tunnel"
    READY = "ready"
    ERROR = "error"


@dataclass
class Project:
    """Represents a generated Expo project instance."""
    id: str
    user_id: str
    prompt: str
    status: ProjectStatus
    directory: str
    port: int
    preview_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    preview_urls: List[str] = field(default_factory=list)  # Store all preview URLs
    
    def to_dict(self) -> dict:
        """Serialize project to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "status": self.status.value,
            "directory": self.directory,
            "port": self.port,
            "preview_url": self.preview_url,
            "error": self.error_message,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "preview_urls": self.preview_urls,
        }


@dataclass
class CodeFile:
    """Represents a single code file in the generated project."""
    path: str
    content: str


@dataclass
class GeneratedCode:
    """Represents the complete generated code structure."""
    files: List[CodeFile]
    dependencies: List[str]
    expo_version: str
    
    def get_main_file(self) -> CodeFile:
        """Get the main App.js or App.tsx file."""
        for file in self.files:
            if file.path in ("App.js", "App.tsx"):
                return file
        raise ValueError("No main App file found in generated code")


@dataclass
class CommandResult:
    """Result of executing a shell command."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float


@dataclass
class SystemMetrics:
    """System resource usage metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_projects: int
    total_projects_created: int
    average_generation_time: float
