"""
Shared Dependencies Manager
Manages a global node_modules directory to avoid redundant installations
"""
import os
import logging
import asyncio
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class SharedDependenciesManager:
    """
    Manages shared node_modules directory for all projects
    
    Uses a single global node_modules that all projects reference via NODE_PATH.
    This eliminates the need for per-project npm installs.
    
    Benefits:
    - Zero npm installs per project
    - Minimal disk space usage
    - Instant project setup
    - Consistent dependency versions
    """
    
    def __init__(self, shared_dir: str = "/tmp/shared_node_modules"):
        """
        Initialize shared dependencies manager
        
        Args:
            shared_dir: Directory for shared node_modules
        """
        self.shared_dir = Path(shared_dir)
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        
        # Global node_modules directory
        self.global_node_modules = self.shared_dir / "global" / "node_modules"
        self.global_node_modules.parent.mkdir(exist_ok=True)
        
        # Lock file for concurrent access
        self.lock_file = self.shared_dir / ".lock"
        
        # Track if global modules are installed
        self.is_initialized = self.global_node_modules.exists()
        
        logger.info(f"Shared dependencies manager initialized: {self.shared_dir}")
        logger.info(f"Global node_modules: {self.global_node_modules}")
    

    
    def get_expo_default_dependencies(self) -> Dict[str, str]:
        """
        Get complete Expo dependencies with ALL UI libraries, styling, animations, and utilities
        
        Returns:
            Dict of default dependencies
        """
        return {
            # ===== CORE EXPO & REACT NATIVE =====
            "expo": "~51.0.0",
            "react": "18.2.0",
            "react-native": "0.74.5",
            "react-native-web": "~0.19.10",
            "react-dom": "18.2.0",
            
            # ===== NAVIGATION & ROUTING =====
            "expo-router": "~3.5.0",
            "expo-linking": "~6.3.0",
            "expo-constants": "~16.0.0",
            "@react-navigation/native": "^6.1.9",
            "@react-navigation/stack": "^6.3.20",
            "@react-navigation/bottom-tabs": "^6.5.11",
            "@react-navigation/drawer": "^6.6.6",
            "react-native-gesture-handler": "~2.16.1",
            "react-native-reanimated": "~3.10.1",
            "react-native-screens": "~3.31.1",
            "react-native-safe-area-context": "4.10.5",
            
            # ===== ICONS & VECTOR GRAPHICS =====
            "@expo/vector-icons": "^14.0.0",  # 15,000+ icons
            "react-native-vector-icons": "^10.0.3",
            
            # ===== UI COMPONENT LIBRARIES =====
            "react-native-paper": "^5.12.3",  # Material Design 3
            "react-native-elements": "^3.4.3",  # UI Toolkit
            "native-base": "^3.4.28",  # Customizable components
            "@tamagui/core": "^1.91.2",  # Lightweight UI
            "dripsy": "^4.3.0",  # Responsive design system
            
            # ===== STYLING & THEMING =====
            "nativewind": "^2.0.11",  # Tailwind CSS for React Native
            "styled-components": "^6.1.8",  # CSS-in-JS
            "expo-linear-gradient": "~13.0.0",  # Gradients
            "react-native-appearance": "^0.3.4",  # Dark mode detection
            
            # ===== ANIMATIONS =====
            "moti": "^0.28.1",  # Easy animations with Reanimated
            "lottie-react-native": "6.7.0",  # Vector animations
            "@shopify/react-native-skia": "^1.0.0",  # Advanced graphics
            
            # ===== FORMS & VALIDATION =====
            "react-hook-form": "^7.51.0",
            "formik": "^2.4.5",
            "yup": "^1.3.3",
            
            # ===== IMAGES & MEDIA =====
            "expo-image": "~1.12.0",
            "expo-image-picker": "~15.0.0",
            "expo-camera": "~15.0.0",
            "expo-media-library": "~16.0.0",
            "react-native-fast-image": "^8.6.3",  # Efficient image caching
            
            # ===== STORAGE & DATA =====
            "@react-native-async-storage/async-storage": "1.23.1",
            "expo-secure-store": "~13.0.0",
            "expo-file-system": "~17.0.0",
            
            # ===== NETWORK & API =====
            "axios": "^1.6.0",
            "expo-network": "~6.0.0",
            
            # ===== SUPABASE (AUTHENTICATION & DATABASE) =====
            "@supabase/supabase-js": "^2.39.0",
            "react-native-url-polyfill": "^2.0.0",  # Required for Supabase
            
            # ===== UX ENHANCERS & FEEDBACK =====
            "react-native-toast-message": "^2.2.0",  # Toast notifications
            "react-native-modal": "^13.0.1",  # Elegant modals
            "@gorhom/bottom-sheet": "^4.6.0",  # Modern bottom sheets
            "react-native-haptic-feedback": "^2.2.0",  # Vibrations
            "expo-haptics": "~13.0.0",  # Expo haptics
            "expo-blur": "~13.0.0",  # Blur effects
            
            # ===== LAYOUT HELPERS =====
            "react-native-responsive-screen": "^1.4.2",  # Screen size handling
            "react-native-size-matters": "^0.4.2",  # Scale fonts/sizes
            
            # ===== FONTS =====
            "expo-font": "~12.0.0",
            "@expo-google-fonts/inter": "^0.2.3",
            "@expo-google-fonts/roboto": "^0.2.3",
            "@expo-google-fonts/poppins": "^0.2.3",
            "@expo-google-fonts/montserrat": "^0.2.3",
            
            # ===== UTILITIES =====
            "expo-status-bar": "~1.12.1",
            "expo-splash-screen": "~0.27.0",
            "expo-device": "~6.0.0",
            "expo-location": "~17.0.0",
            "expo-notifications": "~0.28.0",
            "expo-clipboard": "~6.0.0",
            "expo-sharing": "~12.0.0",
            "expo-web-browser": "~13.0.0",
            "expo-av": "~14.0.0",  # Audio/Video
            "expo-barcode-scanner": "~13.0.0",
            "expo-sensors": "~13.0.0",
            "expo-battery": "~7.0.0",
            "expo-brightness": "~12.0.0",
            "expo-calendar": "~13.0.0",
            "expo-contacts": "~13.0.0",
            "expo-document-picker": "~12.0.0",
            "expo-mail-composer": "~13.0.0",
            "expo-sms": "~12.0.0",
            "expo-speech": "~12.0.0",
            "expo-keep-awake": "~13.0.0",
            
            # ===== DATE & TIME =====
            "date-fns": "^3.3.1",  # Date utilities
            "dayjs": "^1.11.10",  # Lightweight date library
            
            # ===== STATE MANAGEMENT =====
            "zustand": "^4.5.0",  # Simple state management
            "jotai": "^2.6.4",  # Atomic state management
            
            # ===== UTILITIES & HELPERS =====
            "lodash": "^4.17.21",  # Utility functions
            "uuid": "^9.0.1",  # Generate unique IDs
            
            # ===== REQUIRED BY EXPO CLI =====
            "send": "^0.18.0",
            "connect": "^3.7.0",
            "serve-static": "^1.15.0",
            "metro": "^0.80.0",
            "@react-native/metro-config": "^0.74.0"
        }
    
    def get_expo_default_dev_dependencies(self) -> Dict[str, str]:
        """
        Get complete Expo dev dependencies
        
        Returns:
            Dict of default dev dependencies
        """
        return {
            # Babel & TypeScript
            "@babel/core": "^7.20.0",
            "typescript": "^5.1.3",
            
            # Type Definitions
            "@types/react": "~18.2.45",
            "@types/react-native": "^0.73.0",
            "@types/react-dom": "~18.2.0",
            "@types/lodash": "^4.14.202",
            
            # Testing
            "@testing-library/react-native": "^12.4.0",
            "jest": "^29.7.0",
            "jest-expo": "~51.0.0",
            
            # Linting & Formatting
            "eslint": "^8.56.0",
            "prettier": "^3.2.4",
            
            # Environment Variables
            "dotenv": "^16.3.1"
        }
    
    async def ensure_global_modules_installed(self):
        """
        Ensure global node_modules is installed (one-time setup)
        
        This installs all Expo dependencies once in a global location.
        All projects will use this via NODE_PATH.
        """
        if self.is_initialized:
            logger.info("Global node_modules already initialized")
            return str(self.global_node_modules)
        
        logger.info("Installing global node_modules (one-time setup)...")
        
        # Create package.json in global directory
        global_package_json = self.global_node_modules.parent / "package.json"
        
        dependencies = self.get_expo_default_dependencies()
        dev_dependencies = self.get_expo_default_dev_dependencies()
        
        package_data = {
            "name": "shared-expo-dependencies",
            "version": "1.0.0",
            "description": "Shared dependencies for all Expo projects",
            "dependencies": dependencies,
            "devDependencies": dev_dependencies
        }
        
        with open(global_package_json, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        # Install dependencies
        logger.info("Running npm install in global directory...")
        process = await asyncio.create_subprocess_exec(
            "npm", "install", "--legacy-peer-deps",
            cwd=str(self.global_node_modules.parent),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Global npm install failed: {error_msg}")
            raise Exception(f"Failed to install global dependencies: {error_msg}")
        
        self.is_initialized = True
        logger.info(f"✅ Global node_modules installed at {self.global_node_modules}")
        
        return str(self.global_node_modules)
    
    async def setup_project_with_shared_deps(self, project_dir: str) -> str:
        """
        Setup project to use global shared dependencies
        
        This approach:
        1. Ensures global node_modules exists (one-time)
        2. Creates minimal package.json in project
        3. NO npm install in project
        4. Returns NODE_PATH to use when running Expo
        
        Args:
            project_dir: Project directory
            
        Returns:
            Path to global node_modules (for NODE_PATH)
        """
        # Ensure global modules are installed
        await self.ensure_global_modules_installed()
        
        # Create minimal package.json in project (if not exists)
        package_json_path = Path(project_dir) / "package.json"
        
        if not package_json_path.exists():
            # Create minimal package.json (no dependencies listed)
            package_data = {
                "name": Path(project_dir).name,
                "version": "1.0.0",
                "main": "expo-router/entry",
                "scripts": {
                    "start": "expo start",
                    "android": "expo start --android",
                    "ios": "expo start --ios",
                    "web": "expo start --web"
                }
            }
            
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            logger.info(f"Created minimal package.json in {project_dir}")
        
        logger.info(f"✅ Project configured to use global node_modules")
        logger.info(f"   NODE_PATH={self.global_node_modules}")
        
        return str(self.global_node_modules)
    
    def get_global_node_modules_path(self) -> str:
        """
        Get path to global node_modules
        
        Returns:
            Path to global node_modules directory
        """
        return str(self.global_node_modules)
    
    def cleanup_old_caches(self, max_age_days: int = 7):
        """
        Clean up old dependency caches (not used with global approach)
        
        Args:
            max_age_days: Maximum age in days
        """
        logger.info("Cleanup not needed with global node_modules approach")
