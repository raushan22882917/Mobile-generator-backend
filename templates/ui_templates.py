"""
UI Templates System
Provides different color schemes and UI designs for generated apps
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ColorScheme:
    """Color scheme definition"""
    name: str
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    success: str
    warning: str
    error: str
    border: str


@dataclass
class UITemplate:
    """UI template with colors and styling"""
    id: str
    name: str
    description: str
    colors: ColorScheme
    button_style: str
    card_style: str
    input_style: str
    preview_image: str


# Define available templates
TEMPLATES: Dict[str, UITemplate] = {
    "modern_dark": UITemplate(
        id="modern_dark",
        name="Modern Dark",
        description="Sleek dark theme with vibrant accents",
        colors=ColorScheme(
            name="Modern Dark",
            primary="#6366F1",  # Indigo
            secondary="#8B5CF6",  # Purple
            accent="#EC4899",  # Pink
            background="#0F172A",  # Dark blue-gray
            surface="#1E293B",  # Lighter dark
            text_primary="#F1F5F9",  # Light gray
            text_secondary="#94A3B8",  # Medium gray
            success="#10B981",  # Green
            warning="#F59E0B",  # Amber
            error="#EF4444",  # Red
            border="#334155"  # Border gray
        ),
        button_style="rounded-xl shadow-lg",
        card_style="rounded-2xl shadow-xl",
        input_style="rounded-lg border-2",
        preview_image="modern_dark.png"
    ),
    
    "ocean_blue": UITemplate(
        id="ocean_blue",
        name="Ocean Blue",
        description="Calm and professional blue theme",
        colors=ColorScheme(
            name="Ocean Blue",
            primary="#0EA5E9",  # Sky blue
            secondary="#06B6D4",  # Cyan
            accent="#3B82F6",  # Blue
            background="#F0F9FF",  # Very light blue
            surface="#FFFFFF",  # White
            text_primary="#0C4A6E",  # Dark blue
            text_secondary="#475569",  # Slate
            success="#14B8A6",  # Teal
            warning="#F97316",  # Orange
            error="#DC2626",  # Red
            border="#BAE6FD"  # Light blue border
        ),
        button_style="rounded-lg shadow-md",
        card_style="rounded-xl shadow-lg",
        input_style="rounded-md border",
        preview_image="ocean_blue.png"
    ),
    
    "sunset_orange": UITemplate(
        id="sunset_orange",
        name="Sunset Orange",
        description="Warm and energetic orange theme",
        colors=ColorScheme(
            name="Sunset Orange",
            primary="#F97316",  # Orange
            secondary="#FB923C",  # Light orange
            accent="#FBBF24",  # Amber
            background="#FFF7ED",  # Very light orange
            surface="#FFFFFF",  # White
            text_primary="#7C2D12",  # Dark orange
            text_secondary="#78716C",  # Stone
            success="#22C55E",  # Green
            warning="#EAB308",  # Yellow
            error="#DC2626",  # Red
            border="#FED7AA"  # Light orange border
        ),
        button_style="rounded-full shadow-lg",
        card_style="rounded-2xl shadow-md",
        input_style="rounded-full border-2",
        preview_image="sunset_orange.png"
    ),
    
    "forest_green": UITemplate(
        id="forest_green",
        name="Forest Green",
        description="Natural and calming green theme",
        colors=ColorScheme(
            name="Forest Green",
            primary="#10B981",  # Emerald
            secondary="#059669",  # Green
            accent="#14B8A6",  # Teal
            background="#F0FDF4",  # Very light green
            surface="#FFFFFF",  # White
            text_primary="#064E3B",  # Dark green
            text_secondary="#6B7280",  # Gray
            success="#22C55E",  # Green
            warning="#F59E0B",  # Amber
            error="#EF4444",  # Red
            border="#BBF7D0"  # Light green border
        ),
        button_style="rounded-lg shadow-md",
        card_style="rounded-xl shadow-lg",
        input_style="rounded-lg border",
        preview_image="forest_green.png"
    ),
    
    "royal_purple": UITemplate(
        id="royal_purple",
        name="Royal Purple",
        description="Elegant and luxurious purple theme",
        colors=ColorScheme(
            name="Royal Purple",
            primary="#A855F7",  # Purple
            secondary="#C084FC",  # Light purple
            accent="#E879F9",  # Fuchsia
            background="#FAF5FF",  # Very light purple
            surface="#FFFFFF",  # White
            text_primary="#581C87",  # Dark purple
            text_secondary="#6B7280",  # Gray
            success="#10B981",  # Green
            warning="#F59E0B",  # Amber
            error="#DC2626",  # Red
            border="#E9D5FF"  # Light purple border
        ),
        button_style="rounded-xl shadow-lg",
        card_style="rounded-2xl shadow-xl",
        input_style="rounded-lg border-2",
        preview_image="royal_purple.png"
    ),
    
    "minimal_gray": UITemplate(
        id="minimal_gray",
        name="Minimal Gray",
        description="Clean and minimalist gray theme",
        colors=ColorScheme(
            name="Minimal Gray",
            primary="#64748B",  # Slate
            secondary="#94A3B8",  # Light slate
            accent="#475569",  # Dark slate
            background="#F8FAFC",  # Very light gray
            surface="#FFFFFF",  # White
            text_primary="#0F172A",  # Almost black
            text_secondary="#64748B",  # Slate
            success="#10B981",  # Green
            warning="#F59E0B",  # Amber
            error="#EF4444",  # Red
            border="#E2E8F0"  # Light gray border
        ),
        button_style="rounded-md shadow-sm",
        card_style="rounded-lg shadow-md",
        input_style="rounded-md border",
        preview_image="minimal_gray.png"
    ),
    
    "neon_cyber": UITemplate(
        id="neon_cyber",
        name="Neon Cyber",
        description="Futuristic cyberpunk theme with neon colors",
        colors=ColorScheme(
            name="Neon Cyber",
            primary="#06B6D4",  # Cyan
            secondary="#8B5CF6",  # Purple
            accent="#EC4899",  # Pink
            background="#0A0A0A",  # Almost black
            surface="#1A1A1A",  # Dark gray
            text_primary="#00FFFF",  # Cyan
            text_secondary="#A78BFA",  # Light purple
            success="#00FF00",  # Neon green
            warning="#FFFF00",  # Neon yellow
            error="#FF0080",  # Neon pink
            border="#00FFFF"  # Cyan border
        ),
        button_style="rounded-none shadow-[0_0_15px_rgba(6,182,212,0.5)]",
        card_style="rounded-none shadow-[0_0_20px_rgba(139,92,246,0.3)]",
        input_style="rounded-none border-2 shadow-[0_0_10px_rgba(6,182,212,0.3)]",
        preview_image="neon_cyber.png"
    ),
    
    "pastel_dream": UITemplate(
        id="pastel_dream",
        name="Pastel Dream",
        description="Soft and dreamy pastel colors",
        colors=ColorScheme(
            name="Pastel Dream",
            primary="#F9A8D4",  # Pink
            secondary="#C4B5FD",  # Purple
            accent="#A7F3D0",  # Green
            background="#FFFBEB",  # Cream
            surface="#FFFFFF",  # White
            text_primary="#831843",  # Dark pink
            text_secondary="#6B7280",  # Gray
            success="#86EFAC",  # Light green
            warning="#FDE047",  # Light yellow
            error="#FCA5A5",  # Light red
            border="#FBCFE8"  # Light pink border
        ),
        button_style="rounded-full shadow-md",
        card_style="rounded-3xl shadow-lg",
        input_style="rounded-full border",
        preview_image="pastel_dream.png"
    )
}


def get_template(template_id: str) -> UITemplate:
    """Get template by ID"""
    return TEMPLATES.get(template_id)


def get_all_templates() -> List[UITemplate]:
    """Get all available templates"""
    return list(TEMPLATES.values())


def apply_template_to_code(code: str, template: UITemplate) -> str:
    """
    Apply template colors and styles to generated code
    
    Replaces color values and style classes in the code
    """
    colors = template.colors
    
    # Replace common color patterns
    replacements = {
        # Background colors
        "backgroundColor: '#fff'": f"backgroundColor: '{colors.surface}'",
        "backgroundColor: '#ffffff'": f"backgroundColor: '{colors.surface}'",
        "backgroundColor: 'white'": f"backgroundColor: '{colors.surface}'",
        "backgroundColor: '#000'": f"backgroundColor: '{colors.background}'",
        "backgroundColor: '#000000'": f"backgroundColor: '{colors.background}'",
        "backgroundColor: 'black'": f"backgroundColor: '{colors.background}'",
        
        # Text colors
        "color: '#000'": f"color: '{colors.text_primary}'",
        "color: '#000000'": f"color: '{colors.text_primary}'",
        "color: 'black'": f"color: '{colors.text_primary}'",
        "color: '#fff'": f"color: '{colors.text_primary}'",
        "color: '#ffffff'": f"color: '{colors.text_primary}'",
        "color: 'white'": f"color: '{colors.text_primary}'",
        
        # Primary colors
        "backgroundColor: '#007AFF'": f"backgroundColor: '{colors.primary}'",
        "backgroundColor: '#0066CC'": f"backgroundColor: '{colors.primary}'",
        "backgroundColor: 'blue'": f"backgroundColor: '{colors.primary}'",
        
        # Border colors
        "borderColor: '#ccc'": f"borderColor: '{colors.border}'",
        "borderColor: '#ddd'": f"borderColor: '{colors.border}'",
        "borderColor: '#e0e0e0'": f"borderColor: '{colors.border}'",
    }
    
    modified_code = code
    for old, new in replacements.items():
        modified_code = modified_code.replace(old, new)
    
    # Add template colors as constants at the top of the file
    color_constants = f"""
// Template: {template.name}
const COLORS = {{
  primary: '{colors.primary}',
  secondary: '{colors.secondary}',
  accent: '{colors.accent}',
  background: '{colors.background}',
  surface: '{colors.surface}',
  textPrimary: '{colors.text_primary}',
  textSecondary: '{colors.text_secondary}',
  success: '{colors.success}',
  warning: '{colors.warning}',
  error: '{colors.error}',
  border: '{colors.border}',
}};

"""
    
    # Insert color constants after imports
    import_end = modified_code.find('\n\n')
    if import_end != -1:
        modified_code = modified_code[:import_end] + '\n' + color_constants + modified_code[import_end:]
    else:
        modified_code = color_constants + modified_code
    
    return modified_code


def generate_template_stylesheet(template: UITemplate) -> str:
    """Generate a StyleSheet with template colors"""
    colors = template.colors
    
    return f"""import {{ StyleSheet }} from 'react-native';

export const colors = {{
  primary: '{colors.primary}',
  secondary: '{colors.secondary}',
  accent: '{colors.accent}',
  background: '{colors.background}',
  surface: '{colors.surface}',
  textPrimary: '{colors.text_primary}',
  textSecondary: '{colors.text_secondary}',
  success: '{colors.success}',
  warning: '{colors.warning}',
  error: '{colors.error}',
  border: '{colors.border}',
}};

export const styles = StyleSheet.create({{
  container: {{
    flex: 1,
    backgroundColor: colors.background,
  }},
  surface: {{
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: {{ width: 0, height: 2 }},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  }},
  button: {{
    backgroundColor: colors.primary,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  }},
  buttonText: {{
    color: colors.surface,
    fontSize: 16,
    fontWeight: '600',
  }},
  input: {{
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    color: colors.textPrimary,
  }},
  text: {{
    color: colors.textPrimary,
    fontSize: 16,
  }},
  textSecondary: {{
    color: colors.textSecondary,
    fontSize: 14,
  }},
  heading: {{
    color: colors.textPrimary,
    fontSize: 24,
    fontWeight: 'bold',
  }},
  card: {{
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: {{ width: 0, height: 2 }},
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  }},
}});
"""
