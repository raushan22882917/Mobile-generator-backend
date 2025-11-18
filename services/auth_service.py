"""
Firebase Authentication Service
Handles user authentication using Firebase Admin SDK
"""
import os
import logging
from typing import Optional
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.exceptions import FirebaseError

from models.user import User

logger = logging.getLogger(__name__)


class AuthService:
    """Service for Firebase user authentication"""
    
    def __init__(self, firebase_credentials_path: Optional[str] = None):
        """
        Initialize Firebase AuthService
        
        Args:
            firebase_credentials_path: Path to Firebase Admin SDK credentials JSON file
        """
        self.firebase_app = None
        self._initialize_firebase(firebase_credentials_path)
        logger.info("Firebase AuthService initialized")
    
    def _initialize_firebase(self, credentials_path: Optional[str] = None) -> None:
        """
        Initialize Firebase Admin SDK
        
        Args:
            credentials_path: Path to Firebase credentials JSON file
        """
        try:
            # Check if Firebase is already initialized
            try:
                self.firebase_app = firebase_admin.get_app()
                logger.info("Using existing Firebase app instance")
                return
            except ValueError:
                # Firebase not initialized yet, proceed with initialization
                pass
            
            # Initialize Firebase Admin SDK
            # Priority: 1) credentials_path parameter, 2) FIREBASE_CREDENTIALS_PATH env var, 3) GOOGLE_APPLICATION_CREDENTIALS env var
            cred_path = None
            if credentials_path and os.path.exists(credentials_path):
                cred_path = credentials_path
            elif os.getenv("FIREBASE_CREDENTIALS_PATH") and os.path.exists(os.getenv("FIREBASE_CREDENTIALS_PATH")):
                cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
                cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            
            if cred_path:
                cred = credentials.Certificate(cred_path)
                self.firebase_app = firebase_admin.initialize_app(cred)
                logger.info(f"Firebase initialized with credentials from {cred_path}")
            else:
                # Try to use default credentials (for Google Cloud environments)
                try:
                    self.firebase_app = firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
                except Exception as e:
                    logger.warning(f"Could not initialize Firebase with default credentials: {e}")
                    logger.warning("Firebase authentication will not be available")
                    self.firebase_app = None
                    
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.firebase_app = None
    
    def verify_token(self, id_token: str) -> Optional[User]:
        """
        Verify Firebase ID token and return User
        
        Args:
            id_token: Firebase ID token string
            
        Returns:
            User instance if token is valid, None otherwise
        """
        if not self.firebase_app:
            logger.error("Firebase not initialized, cannot verify token")
            return None
        
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extract user information from token
            uid = decoded_token.get('uid')
            email = decoded_token.get('email', '')
            name = decoded_token.get('name') or decoded_token.get('display_name')
            
            # Get additional user info from Firebase Auth
            try:
                firebase_user = auth.get_user(uid)
                if not name:
                    name = firebase_user.display_name
                if not email:
                    email = firebase_user.email or ''
            except FirebaseError as e:
                logger.warning(f"Could not fetch user details from Firebase: {e}")
            
            # Create User instance from Firebase data
            user = User(
                id=uid,
                email=email,
                password_hash="",  # Firebase handles passwords, we don't store them
                name=name,
                created_at=datetime.fromtimestamp(decoded_token.get('iat', 0)) if decoded_token.get('iat') else datetime.now(),
                last_login=datetime.now(),
                is_active=True
            )
            
            logger.debug(f"Token verified for user: {email} (UID: {uid})")
            return user
            
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid Firebase ID token: {e}")
            return None
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired Firebase ID token: {e}")
            return None
        except FirebaseError as e:
            logger.error(f"Firebase error verifying token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by Firebase UID
        
        Args:
            user_id: Firebase user UID
            
        Returns:
            User instance if found, None otherwise
        """
        if not self.firebase_app:
            return None
        
        try:
            firebase_user = auth.get_user(user_id)
            
            user = User(
                id=firebase_user.uid,
                email=firebase_user.email or '',
                password_hash="",  # Firebase handles passwords
                name=firebase_user.display_name,
                created_at=datetime.fromtimestamp(firebase_user.user_metadata.creation_timestamp / 1000) if firebase_user.user_metadata.creation_timestamp else datetime.now(),
                last_login=datetime.fromtimestamp(firebase_user.user_metadata.last_sign_in_timestamp / 1000) if firebase_user.user_metadata.last_sign_in_timestamp else None,
                is_active=not firebase_user.disabled
            )
            
            return user
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {user_id}")
            return None
        except FirebaseError as e:
            logger.error(f"Firebase error getting user: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            email: User email address
            
        Returns:
            User instance if found, None otherwise
        """
        if not self.firebase_app:
            return None
        
        try:
            firebase_user = auth.get_user_by_email(email)
            
            user = User(
                id=firebase_user.uid,
                email=firebase_user.email or '',
                password_hash="",  # Firebase handles passwords
                name=firebase_user.display_name,
                created_at=datetime.fromtimestamp(firebase_user.user_metadata.creation_timestamp / 1000) if firebase_user.user_metadata.creation_timestamp else datetime.now(),
                last_login=datetime.fromtimestamp(firebase_user.user_metadata.last_sign_in_timestamp / 1000) if firebase_user.user_metadata.last_sign_in_timestamp else None,
                is_active=not firebase_user.disabled
            )
            
            return user
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {email}")
            return None
        except FirebaseError as e:
            logger.error(f"Firebase error getting user by email: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user by email: {e}")
            return None
