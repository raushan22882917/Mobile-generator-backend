"""
User model for authentication
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib
import secrets


@dataclass
class User:
    """Represents a user account"""
    id: str
    email: str
    password_hash: str  # Hashed password, never store plain text
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self, include_password: bool = False) -> dict:
        """Serialize user to dictionary"""
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }
        if include_password:
            data["password_hash"] = self.password_hash
        return data
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 with salt"""
        # Generate a salt
        salt = secrets.token_hex(16)
        # Hash password with salt
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        # Return salt:hash format
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against a hash"""
        try:
            salt, stored_hash = password_hash.split(":", 1)
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == stored_hash
        except ValueError:
            return False

