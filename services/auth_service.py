"""
Authentication Service
Handles user authentication, JWT token generation, and user management
"""
import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import jwt
from jwt.exceptions import InvalidTokenError

from models.user import User
from exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# JWT Secret Key (should be in environment variable in production)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days


class AuthService:
    """Service for user authentication and JWT token management"""
    
    def __init__(self, users_dir: str = "/tmp/users"):
        """
        Initialize AuthService
        
        Args:
            users_dir: Directory to store user data
        """
        self.users_dir = Path(users_dir)
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.users_dir / "users.json"
        self.users: Dict[str, User] = {}
        self._load_users()
        logger.info(f"AuthService initialized with {len(self.users)} users")
    
    def _load_users(self) -> None:
        """Load users from JSON file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    for user_data in users_data:
                        user = User(
                            id=user_data['id'],
                            email=user_data['email'],
                            password_hash=user_data['password_hash'],
                            name=user_data.get('name'),
                            created_at=datetime.fromisoformat(user_data['created_at']),
                            last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None,
                            is_active=user_data.get('is_active', True)
                        )
                        self.users[user.id] = user
                logger.info(f"Loaded {len(self.users)} users from {self.users_file}")
            except Exception as e:
                logger.error(f"Failed to load users: {e}")
                self.users = {}
        else:
            logger.info("No users file found, starting with empty user database")
    
    def _save_users(self) -> None:
        """Save users to JSON file"""
        try:
            users_data = [user.to_dict(include_password=True) for user in self.users.values()]
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, default=str)
            logger.debug(f"Saved {len(self.users)} users to {self.users_file}")
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def register_user(self, email: str, password: str, name: Optional[str] = None) -> User:
        """
        Register a new user
        
        Args:
            email: User email
            password: Plain text password (will be hashed)
            name: Optional user name
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        for user in self.users.values():
            if user.email.lower() == email.lower():
                raise ValueError("Email already registered")
        
        # Validate password
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = User.hash_password(password)
        
        user = User(
            id=user_id,
            email=email.lower(),
            password_hash=password_hash,
            name=name,
            created_at=datetime.now(),
            is_active=True
        )
        
        self.users[user.id] = user
        self._save_users()
        
        logger.info(f"New user registered: {email} (ID: {user_id})")
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        # Find user by email
        user = None
        for u in self.users.values():
            if u.email.lower() == email.lower():
                user = u
                break
        
        if not user:
            logger.warning(f"Authentication failed: User not found - {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: User inactive - {email}")
            return None
        
        # Verify password
        if not User.verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed: Invalid password - {email}")
            return None
        
        # Update last login
        user.last_login = datetime.now()
        self._save_users()
        
        logger.info(f"User authenticated: {email}")
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    def generate_token(self, user: User) -> str:
        """
        Generate JWT token for user
        
        Args:
            user: User instance
            
        Returns:
            JWT token string
        """
        payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    
    def verify_token(self, token: str) -> Optional[User]:
        """
        Verify JWT token and return user
        
        Args:
            token: JWT token string
            
        Returns:
            User instance if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("user_id")
            
            if not user_id:
                return None
            
            user = self.get_user_by_id(user_id)
            if user and user.is_active:
                return user
            
            return None
            
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def update_user(self, user_id: str, name: Optional[str] = None) -> Optional[User]:
        """
        Update user information
        
        Args:
            user_id: User ID
            name: Optional new name
            
        Returns:
            Updated User instance or None if not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if name is not None:
            user.name = name
        
        self._save_users()
        return user

