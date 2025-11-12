"""
UI/UX Design Principles for AI-Generated Mobile Apps
This module provides design guidelines and utilities for generating professional mobile interfaces
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IconMapping:
    """Maps screen types and features to appropriate icons"""
    screen_type: str
    icon_name: str
    icon_library: str = "MaterialIcons"  # Default to MaterialIcons from @expo/vector-icons
    color: Optional[str] = None


class UIUXDesignPrinciples:
    """
    UI/UX Design Principles and Guidelines
    
    This class provides design guidelines, icon mappings, and best practices
    for generating professional mobile app interfaces.
    """
    
    # Icon mappings for common screen types and features
    ICON_MAPPINGS: Dict[str, IconMapping] = {
        # Navigation & Core Screens
        "home": IconMapping("home", "home", "MaterialIcons", "#2196F3"),
        "index": IconMapping("index", "home", "MaterialIcons", "#2196F3"),
        "profile": IconMapping("profile", "person", "MaterialIcons", "#4CAF50"),
        "settings": IconMapping("settings", "settings", "MaterialIcons", "#757575"),
        "login": IconMapping("login", "login", "MaterialIcons", "#2196F3"),
        "signup": IconMapping("signup", "person-add", "MaterialIcons", "#4CAF50"),
        "dashboard": IconMapping("dashboard", "dashboard", "MaterialIcons", "#2196F3"),
        
        # Common Features
        "search": IconMapping("search", "search", "MaterialIcons", "#757575"),
        "notifications": IconMapping("notifications", "notifications", "MaterialIcons", "#FF9800"),
        "favorites": IconMapping("favorites", "favorite", "MaterialIcons", "#E91E63"),
        "cart": IconMapping("cart", "shopping-cart", "MaterialIcons", "#FF5722"),
        "history": IconMapping("history", "history", "MaterialIcons", "#9E9E9E"),
        "help": IconMapping("help", "help", "MaterialIcons", "#2196F3"),
        "about": IconMapping("about", "info", "MaterialIcons", "#2196F3"),
        
        # Content Types
        "weather": IconMapping("weather", "wb-sunny", "MaterialIcons", "#FFC107"),
        "fitness": IconMapping("fitness", "fitness-center", "MaterialIcons", "#4CAF50"),
        "health": IconMapping("health", "favorite", "MaterialIcons", "#E91E63"),
        "finance": IconMapping("finance", "account-balance-wallet", "MaterialIcons", "#4CAF50"),
        "education": IconMapping("education", "school", "MaterialIcons", "#2196F3"),
        "music": IconMapping("music", "music-note", "MaterialIcons", "#9C27B0"),
        "video": IconMapping("video", "video-library", "MaterialIcons", "#E91E63"),
        "news": IconMapping("news", "article", "MaterialIcons", "#FF5722"),
        "social": IconMapping("social", "people", "MaterialIcons", "#2196F3"),
        "shopping": IconMapping("shopping", "shopping-bag", "MaterialIcons", "#FF5722"),
        "food": IconMapping("food", "restaurant", "MaterialIcons", "#FF9800"),
        "travel": IconMapping("travel", "flight", "MaterialIcons", "#03A9F4"),
        "calendar": IconMapping("calendar", "calendar-today", "MaterialIcons", "#2196F3"),
        "tasks": IconMapping("tasks", "check-circle", "MaterialIcons", "#4CAF50"),
        "notes": IconMapping("notes", "note", "MaterialIcons", "#FFC107"),
    }
    
    # Design color palette (Material Design inspired)
    COLOR_PALETTE = {
        "primary": "#2196F3",      # Blue
        "secondary": "#4CAF50",   # Green
        "accent": "#FF9800",      # Orange
        "error": "#F44336",       # Red
        "warning": "#FFC107",     # Amber
        "success": "#4CAF50",     # Green
        "info": "#2196F3",        # Blue
        "background": "#FFFFFF",
        "surface": "#F5F5F5",
        "text_primary": "#212121",
        "text_secondary": "#757575",
        "divider": "#BDBDBD",
    }
    
    # Spacing system (8px grid)
    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48,
    }
    
    # Typography scale
    TYPOGRAPHY = {
        "h1": {"size": 32, "weight": "bold"},
        "h2": {"size": 24, "weight": "bold"},
        "h3": {"size": 20, "weight": "600"},
        "h4": {"size": 18, "weight": "600"},
        "body": {"size": 16, "weight": "normal"},
        "caption": {"size": 14, "weight": "normal"},
        "small": {"size": 12, "weight": "normal"},
    }
    
    @staticmethod
    def get_icon_for_screen(screen_name: str, screen_description: str = "") -> Optional[IconMapping]:
        """
        Get appropriate icon for a screen based on its name and description
        
        Args:
            screen_name: Name of the screen (e.g., "home", "profile")
            screen_description: Optional description of the screen
            
        Returns:
            IconMapping object or None if no match found
        """
        screen_lower = screen_name.lower()
        
        # Direct match
        if screen_lower in UIUXDesignPrinciples.ICON_MAPPINGS:
            return UIUXDesignPrinciples.ICON_MAPPINGS[screen_lower]
        
        # Partial match in description
        description_lower = screen_description.lower()
        for key, icon_mapping in UIUXDesignPrinciples.ICON_MAPPINGS.items():
            if key in description_lower or description_lower in key:
                return icon_mapping
        
        # Default to home icon if no match
        return UIUXDesignPrinciples.ICON_MAPPINGS.get("home")
    
    @staticmethod
    def get_icon_import_statement() -> str:
        """
        Get the import statement for @expo/vector-icons
        
        Returns:
            Import statement string
        """
        return "import { MaterialIcons, Ionicons, FontAwesome, AntDesign } from '@expo/vector-icons';"
    
    @staticmethod
    def get_icon_component_code(icon_mapping: IconMapping, size: int = 24) -> str:
        """
        Generate React Native code for an icon component
        
        Args:
            icon_mapping: IconMapping object
            size: Icon size in pixels
            
        Returns:
            React Native component code string
        """
        library = icon_mapping.icon_library
        icon_name = icon_mapping.icon_name
        color = icon_mapping.color or UIUXDesignPrinciples.COLOR_PALETTE["primary"]
        
        return f'<{library} name="{icon_name}" size={size} color="{color}" />'
    
    @staticmethod
    def get_design_guidelines() -> Dict:
        """
        Get comprehensive UI/UX design guidelines
        
        Returns:
            Dictionary with design guidelines
        """
        return {
            "spacing": {
                "use_8px_grid": True,
                "standard_spacing": UIUXDesignPrinciples.SPACING,
                "guideline": "Use multiples of 8px for consistent spacing"
            },
            "typography": {
                "scale": UIUXDesignPrinciples.TYPOGRAPHY,
                "guideline": "Use consistent typography scale for hierarchy"
            },
            "colors": {
                "palette": UIUXDesignPrinciples.COLOR_PALETTE,
                "guideline": "Use Material Design color palette for consistency"
            },
            "icons": {
                "library": "@expo/vector-icons",
                "libraries_available": ["MaterialIcons", "Ionicons", "FontAwesome", "AntDesign"],
                "guideline": "Use appropriate icons from @expo/vector-icons for better UX"
            },
            "components": {
                "use_touchable": True,
                "use_safe_area": True,
                "use_keyboard_avoiding": True,
                "guideline": "Always use TouchableOpacity, SafeAreaView, and KeyboardAvoidingView for better UX"
            },
            "accessibility": {
                "add_labels": True,
                "use_semantic_elements": True,
                "guideline": "Always add accessibility labels and use semantic HTML elements"
            }
        }
    
    @staticmethod
    def generate_icon_suggestions(screen_content: str) -> List[str]:
        """
        Analyze screen content and suggest appropriate icons
        
        Args:
            screen_content: The screen's code or description
            
        Returns:
            List of suggested icon names
        """
        content_lower = screen_content.lower()
        suggestions = []
        
        # Check for common patterns
        for key, icon_mapping in UIUXDesignPrinciples.ICON_MAPPINGS.items():
            if key in content_lower:
                suggestions.append(icon_mapping.icon_name)
        
        # Remove duplicates and return
        return list(set(suggestions))[:5]  # Max 5 suggestions


# Export commonly used functions
def get_icon_for_screen(screen_name: str, description: str = "") -> Optional[IconMapping]:
    """Convenience function to get icon for a screen"""
    return UIUXDesignPrinciples.get_icon_for_screen(screen_name, description)


def get_icon_import() -> str:
    """Convenience function to get icon import statement"""
    return UIUXDesignPrinciples.get_icon_import_statement()

