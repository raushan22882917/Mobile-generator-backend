"""
Data models for projects, code generation, and system metrics.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict


class ProjectStatus(Enum):
    """Status of a project during its lifecycle."""
    INITIALIZING = "initializing"
    GENERATING_CODE = "generating_code"
    INSTALLING_DEPS = "installing_deps"
    STARTING_SERVER = "starting_server"
    CREATING_TUNNEL = "creating_tunnel"
    READY = "ready"
    ERROR = "error"


class BuildStepStatus(Enum):
    """Status of individual build steps"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BuildStep:
    """Represents a single step in the build process"""
    id: str
    name: str
    description: str
    status: BuildStepStatus
    progress: int = 0  # 0-100
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class TunnelURL:
    """Represents a tunnel URL with metadata"""
    url: str
    created_at: datetime
    is_active: bool = True
    port: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "url": self.url,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "port": self.port
        }


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
    preview_urls: List[str] = field(default_factory=list)  # Store all preview URLs (legacy)
    tunnel_urls: List[TunnelURL] = field(default_factory=list)  # Store all tunnel URLs with metadata
    build_steps: List[BuildStep] = field(default_factory=list)  # Track build progress steps
    
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
            "tunnel_urls": [tunnel.to_dict() for tunnel in self.tunnel_urls],
        }
    
    def add_tunnel_url(self, url: str, port: Optional[int] = None) -> None:
        """Add a new tunnel URL with timestamp"""
        tunnel = TunnelURL(
            url=url,
            created_at=datetime.now(),
            is_active=True,
            port=port
        )
        self.tunnel_urls.append(tunnel)
        # Also update preview_url and preview_urls for backward compatibility
        self.preview_url = url
        if url not in self.preview_urls:
            self.preview_urls.append(url)
        self.last_active = datetime.now()
    
    def get_active_tunnel_urls(self) -> List[TunnelURL]:
        """Get all active tunnel URLs"""
        return [tunnel for tunnel in self.tunnel_urls if tunnel.is_active]
    
    def get_latest_tunnel_url(self) -> Optional[str]:
        """Get the most recent tunnel URL"""
        if self.tunnel_urls:
            return self.tunnel_urls[-1].url
        return self.preview_url


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
