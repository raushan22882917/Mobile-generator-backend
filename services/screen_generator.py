"""
Screen Generator Service
AI-powered automatic screen generation based on app requirements
"""
import asyncio
import logging
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class ImageRequirement:
    """Represents an image that should be generated"""
    description: str
    filename: str
    purpose: str  # e.g., "logo", "hero", "icon", "background"


@dataclass
class ScreenDefinition:
    """Represents a screen to be generated"""
    name: str
    file_name: str
    location: str  # 'tabs' or 'app'
    description: str
    content: str
    images_needed: List[ImageRequirement] = field(default_factory=list)


class ScreenGenerator:
    """Service for AI-powered screen generation"""
    
    def __init__(self, api_key: str, model: str = "gpt-5", gemini_api_key: str = None):
        """
        Initialize the ScreenGenerator
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            gemini_api_key: Gemini API key for image generation (optional)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
        # Initialize image generator
        from services.gemini_image import AIImageGenerator
        self.image_generator = AIImageGenerator(
            gemini_api_key=gemini_api_key,
            openai_api_key=api_key
        )
        
        logger.info("ScreenGenerator initialized with image generation support")
    
    async def analyze_prompt_suggestions(self, prompt: str) -> Dict:
        """
        Analyze prompt and return suggested screens and images WITHOUT generating them
        
        Args:
            prompt: User's app description
            
        Returns:
            Dictionary with suggested screens and images
        """
        logger.info("Analyzing prompt for suggestions")
        
        # Analyze screens and images in parallel
        screens_task = self._analyze_required_screens(prompt)
        images_task = self._analyze_required_images(prompt)
        
        screens, images = await asyncio.gather(screens_task, images_task)
        
        return {
            "screens": screens,
            "images": [
                {
                    "description": img.description,
                    "filename": img.filename,
                    "purpose": img.purpose
                }
                for img in images
            ],
            "total_screens": len(screens),
            "total_images": len(images)
        }
    
    async def analyze_and_generate_screens(
        self, 
        prompt: str,
        generate_images: bool = True
    ) -> List[ScreenDefinition]:
        """
        Analyze the prompt and generate all necessary screens with images
        
        Args:
            prompt: User's app description
            generate_images: Whether to generate images (default: True)
            
        Returns:
            List of ScreenDefinition objects
        """
        logger.info("Analyzing prompt to determine required screens and images")
        
        # Step 1: Analyze prompt to determine screens and images
        screen_analysis = await self._analyze_required_screens(prompt)
        
        # Step 2: Analyze what images are needed
        image_requirements = []
        if generate_images:
            image_requirements = await self._analyze_required_images(prompt)
            logger.info(f"Identified {len(image_requirements)} images to generate")
        
        # Step 3: Generate content for each screen in parallel
        screen_tasks = [
            self._generate_screen_content(screen_info, prompt, image_requirements)
            for screen_info in screen_analysis
        ]
        
        screens = await asyncio.gather(*screen_tasks)
        
        logger.info(f"Generated {len(screens)} screens")
        return screens
    
    async def _analyze_required_images(self, prompt: str) -> List[ImageRequirement]:
        """
        Use AI to analyze what images are needed for the app
        
        Args:
            prompt: User's app description
            
        Returns:
            List of ImageRequirement objects
        """
        analysis_prompt = f"""Analyze this mobile app description and determine what images should be generated.

App Description: {prompt}

Determine what images would enhance the app:
- App logo/icon
- Hero images for screens
- Background images
- Illustrations
- Icons

IMPORTANT:
- Only suggest images that are truly needed
- Maximum 3-5 images total
- Be specific about what each image should show
- Consider the app's theme and purpose

Respond in this exact JSON format:
{{
  "images": [
    {{
      "description": "Modern fitness app logo with dumbbell icon, blue and orange gradient",
      "filename": "app-logo.png",
      "purpose": "logo"
    }},
    {{
      "description": "Hero image showing person exercising outdoors, motivational",
      "filename": "hero-workout.png",
      "purpose": "hero"
    }}
  ]
}}

Respond with ONLY the JSON, no other text."""

        try:
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.model,
                    input=analysis_prompt
                ),
                timeout=60
            )
            
            import json
            import re
            
            response_text = response.output_text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)
            
            analysis = json.loads(response_text)
            images = analysis.get('images', [])
            
            # Convert to ImageRequirement objects
            image_requirements = [
                ImageRequirement(
                    description=img['description'],
                    filename=img['filename'],
                    purpose=img.get('purpose', 'general')
                )
                for img in images
            ]
            
            logger.info(f"Identified {len(image_requirements)} images to generate")
            return image_requirements
            
        except Exception as e:
            logger.warning(f"Error analyzing images: {e}, skipping image generation")
            return []
    
    async def _analyze_required_screens(self, prompt: str) -> List[Dict]:
        """
        Use AI to analyze what screens are needed
        
        Args:
            prompt: User's app description
            
        Returns:
            List of screen information dictionaries
        """
        analysis_prompt = f"""Analyze this mobile app description and determine what screens are needed.

App Description: {prompt}

For a React Native Expo app with tab navigation, determine:
1. What tab screens are needed (these go in app/(tabs)/)
2. Tab screens should be named descriptively (e.g., home.tsx, profile.tsx, settings.tsx)

IMPORTANT RULES:
- Tab screens go in app/(tabs)/ location
- Tab screens should be named descriptively (e.g., home.tsx, profile.tsx, settings.tsx)
- Minimum 2 tab screens, maximum 5 tab screens
- Use lowercase with hyphens for multi-word names (e.g., user-profile.tsx)
- First screen should always be index.tsx (home screen)

Respond in this exact JSON format:
{{
  "screens": [
    {{
      "name": "Home",
      "file_name": "index.tsx",
      "location": "tabs",
      "description": "Main home screen showing..."
    }},
    {{
      "name": "Profile",
      "file_name": "profile.tsx",
      "location": "tabs",
      "description": "User profile and settings"
    }}
  ]
}}

Respond with ONLY the JSON, no other text."""

        try:
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.model,
                    input=analysis_prompt
                ),
                timeout=60
            )
            
            # Parse JSON response
            import json
            import re
            
            response_text = response.output_text.strip()
            
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)
            
            analysis = json.loads(response_text)
            screens = analysis.get('screens', [])
            
            # Ensure tab screens are in tabs location
            for screen in screens:
                if screen.get('location') != 'app':
                    screen['location'] = 'tabs'
            
            # Always add login and signup screens in app/ folder (same level as modal.tsx)
            screens.extend([
                {
                    "name": "Login",
                    "file_name": "login.tsx",
                    "location": "app",
                    "description": "User login screen with email and password"
                },
                {
                    "name": "Signup",
                    "file_name": "signup.tsx",
                    "location": "app",
                    "description": "User registration screen with form fields"
                }
            ])
            
            logger.info(f"Identified {len(screens)} screens to generate (including login/signup)")
            return screens
            
        except Exception as e:
            logger.error(f"Error analyzing screens: {e}")
            # Fallback to default screens
            return [
                {
                    "name": "Home",
                    "file_name": "index.tsx",
                    "location": "tabs",
                    "description": "Main home screen"
                },
                {
                    "name": "Explore",
                    "file_name": "explore.tsx",
                    "location": "tabs",
                    "description": "Explore and discover content"
                },
                {
                    "name": "Profile",
                    "file_name": "profile.tsx",
                    "location": "tabs",
                    "description": "User profile and settings"
                },
                {
                    "name": "Login",
                    "file_name": "login.tsx",
                    "location": "app",
                    "description": "User login screen with email and password"
                },
                {
                    "name": "Signup",
                    "file_name": "signup.tsx",
                    "location": "app",
                    "description": "User registration screen with form fields"
                }
            ]
    
    async def _generate_screen_content(
        self,
        screen_info: Dict,
        app_prompt: str,
        image_requirements: List[ImageRequirement] = None
    ) -> ScreenDefinition:
        """
        Generate the actual code content for a screen
        
        Args:
            screen_info: Screen information dictionary
            app_prompt: Original app description
            
        Returns:
            ScreenDefinition with generated content
        """
        screen_name = screen_info['name']
        file_name = screen_info['file_name']
        location = screen_info['location']
        description = screen_info['description']
        
        logger.info(f"Generating content for {screen_name} screen")
        
        # Build image context if available
        image_context = ""
        if image_requirements:
            image_list = "\n".join([
                f"- {img.filename}: {img.description} (for {img.purpose})"
                for img in image_requirements
            ])
            image_context = f"""

Available Images (will be generated):
{image_list}

You can reference these images in your code using:
import {{ Image }} from 'react-native';
<Image source={{require('@/assets/images/{image_requirements[0].filename}')}} />
"""
        
        # Get appropriate icon for this screen using UI/UX principles
        from utils.ui_ux_principles import get_icon_for_screen, get_icon_import
        icon_mapping = get_icon_for_screen(screen_name, description)
        icon_context = ""
        if icon_mapping:
            icon_context = f"""
- Use @expo/vector-icons for professional icons
- Import: {get_icon_import()}
- Primary icon for this screen: {icon_mapping.icon_library}.{icon_mapping.icon_name} (color: {icon_mapping.color or '#2196F3'})
- Use icons appropriately throughout the UI (buttons, headers, list items, etc.)
- Example: <{icon_mapping.icon_library} name="{icon_mapping.icon_name}" size={24} color="{icon_mapping.color or '#2196F3'}" />
"""
        
        generation_prompt = f"""Generate a complete React Native Expo screen component with DUMMY DATA.

App Context: {app_prompt}

Screen Details:
- Name: {screen_name}
- Purpose: {description}
- Location: app/({location})/{file_name}
{image_context}
{icon_context}

Requirements:
- Use TypeScript (.tsx)
- Use functional components with hooks
- Import from '@/components/themed-text' and '@/components/themed-view'
- Use StyleSheet for styling
- Include proper imports from 'react-native'
- MUST include @expo/vector-icons import and use icons throughout the UI
- MUST include realistic dummy/placeholder data (arrays, objects, sample text)
- If images are available, use them appropriately in the UI
- Make it visually appealing and functional with sample data
- Add cards, lists, or UI elements with dummy content
- Use icons in buttons, headers, navigation, and list items for better UX
- Follow Material Design principles for spacing and typography
- Export default function

Generate ONLY the complete TypeScript code with dummy data, no explanations."""

        try:
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.model,
                    input=generation_prompt
                ),
                timeout=90
            )
            
            content = response.output_text.strip()
            
            # Clean up code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                # Remove first line (```typescript or similar)
                lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines)
            
            # Determine which images this screen should use
            screen_images = []
            if image_requirements:
                # Assign relevant images based on screen type
                if 'home' in screen_name.lower() or 'index' in file_name:
                    # Home screen gets logo and hero images
                    screen_images = [img for img in image_requirements 
                                   if img.purpose in ['logo', 'hero']]
                elif 'auth' in file_name.lower():
                    # Auth screen gets logo
                    screen_images = [img for img in image_requirements 
                                   if img.purpose == 'logo']
            
            return ScreenDefinition(
                name=screen_name,
                file_name=file_name,
                location=location,
                description=description,
                content=content,
                images_needed=screen_images
            )
            
        except Exception as e:
            logger.error(f"Error generating screen {screen_name}: {e}")
            # Return a basic template
            return self._create_fallback_screen(screen_info)
    
    def _create_fallback_screen(self, screen_info: Dict) -> ScreenDefinition:
        """Create a basic fallback screen if generation fails"""
        screen_name = screen_info['name']
        file_name = screen_info['file_name']
        location = screen_info['location']
        description = screen_info['description']
        
        content = f"""import {{ StyleSheet, ScrollView }} from 'react-native';
import {{ ThemedText }} from '@/components/themed-text';
import {{ ThemedView }} from '@/components/themed-view';

export default function {screen_name.replace(' ', '')}Screen() {{
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <ThemedView style={styles.content}>
        <ThemedText type="title">{screen_name}</ThemedText>
        <ThemedText type="default" style={styles.description}>
          {description}
        </ThemedText>
      </ThemedView>
    </ScrollView>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
    padding: 16,
  }},
  content: {{
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  }},
  description: {{
    textAlign: 'center',
    opacity: 0.7,
  }},
}});
"""
        
        return ScreenDefinition(
            name=screen_name,
            file_name=file_name,
            location=location,
            description=description,
            content=content
        )
    
    async def generate_images_for_project(
        self,
        screens: List[ScreenDefinition],
        project_dir: str
    ) -> Dict[str, str]:
        """
        Generate all required images for the screens
        
        Args:
            screens: List of ScreenDefinition objects
            project_dir: Path to the project directory
            
        Returns:
            Dictionary mapping filename to file path
        """
        # Collect all unique images needed
        all_images = {}
        for screen in screens:
            for img in screen.images_needed:
                if img.filename not in all_images:
                    all_images[img.filename] = img
        
        if not all_images:
            logger.info("No images to generate")
            return {}
        
        logger.info(f"Generating {len(all_images)} images in parallel")
        
        # Generate images in parallel
        image_tasks = [
            self._generate_single_image(img, project_dir)
            for img in all_images.values()
        ]
        
        results = await asyncio.gather(*image_tasks, return_exceptions=True)
        
        # Build result dictionary
        generated_images = {}
        for img, result in zip(all_images.values(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate {img.filename}: {result}")
            elif result:
                generated_images[img.filename] = result
                logger.info(f"Generated image: {img.filename}")
        
        return generated_images
    
    async def _generate_single_image(
        self,
        image_req: ImageRequirement,
        project_dir: str
    ) -> Optional[str]:
        """
        Generate a single image
        
        Args:
            image_req: ImageRequirement object
            project_dir: Path to project directory
            
        Returns:
            Path to generated image or None
        """
        try:
            logger.info(f"Generating image: {image_req.filename}")
            
            # Run image generation in executor (it's blocking)
            loop = asyncio.get_event_loop()
            image_data, provider = await loop.run_in_executor(
                None,
                self.image_generator.generate_image,
                image_req.description
            )
            
            if not image_data:
                logger.error(f"Failed to generate image: {provider}")
                return None
            
            # Save image to project
            file_path = self.image_generator.save_image_to_project(
                project_dir,
                image_data,
                image_req.filename
            )
            
            logger.info(f"Saved image to: {file_path} (provider: {provider})")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating image {image_req.filename}: {e}")
            return None
    
    def write_screens_to_project(
        self,
        screens: List[ScreenDefinition],
        project_dir: str
    ) -> List[str]:
        """
        Write generated screens to the project directory
        
        Args:
            screens: List of ScreenDefinition objects
            project_dir: Path to the project directory
            
        Returns:
            List of created file paths
        """
        created_files = []
        tab_screens = []
        
        for screen in screens:
            if screen.location == 'tabs':
                file_path = os.path.join(project_dir, 'app', '(tabs)', screen.file_name)
                tab_screens.append(screen)
            else:
                file_path = os.path.join(project_dir, 'app', screen.file_name)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(screen.content)
                
                created_files.append(file_path)
                logger.info(f"Created screen: {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to write screen {screen.file_name}: {e}")
        
        # Update _layout.tsx in tabs folder with all tab screens
        if tab_screens:
            layout_path = os.path.join(project_dir, 'app', '(tabs)', '_layout.tsx')
            try:
                layout_content = self._generate_tabs_layout(tab_screens)
                with open(layout_path, 'w', encoding='utf-8') as f:
                    f.write(layout_content)
                created_files.append(layout_path)
                logger.info(f"Updated tabs layout: {layout_path}")
            except Exception as e:
                logger.error(f"Failed to write _layout.tsx: {e}")
        
        # Also create/update modal.tsx as welcome screen
        modal_path = os.path.join(project_dir, 'app', 'modal.tsx')
        try:
            modal_content = self._generate_welcome_modal()
            with open(modal_path, 'w', encoding='utf-8') as f:
                f.write(modal_content)
            created_files.append(modal_path)
            logger.info(f"Created welcome modal: {modal_path}")
        except Exception as e:
            logger.error(f"Failed to write modal.tsx: {e}")
        
        return created_files
    
    def _generate_tabs_layout(self, tab_screens: List[ScreenDefinition]) -> str:
        """Generate _layout.tsx for tabs with all screen names"""
        
        # Map screen names to appropriate icons
        icon_map = {
            'home': 'house.fill',
            'index': 'house.fill',
            'explore': 'paperplane.fill',
            'search': 'magnifyingglass',
            'profile': 'person.fill',
            'settings': 'gearshape.fill',
            'favorites': 'heart.fill',
            'notifications': 'bell.fill',
            'messages': 'message.fill',
            'calendar': 'calendar',
            'stats': 'chart.bar.fill',
            'activity': 'flame.fill',
        }
        
        # Generate Tabs.Screen entries
        tab_entries = []
        for screen in tab_screens:
            # Get screen name without .tsx
            screen_file = screen.file_name.replace('.tsx', '')
            screen_title = screen.name
            
            # Find appropriate icon
            icon_name = 'circle.fill'  # default icon
            for key, icon in icon_map.items():
                if key in screen_file.lower() or key in screen_title.lower():
                    icon_name = icon
                    break
            
            tab_entry = f'''      <Tabs.Screen
        name="{screen_file}"
        options={{{{
          title: '{screen_title}',
          tabBarIcon: ({{ color }}) => <IconSymbol size={{28}} name="{icon_name}" color={{color}} />,
        }}}}
      />'''
            tab_entries.append(tab_entry)
        
        tabs_content = '\n'.join(tab_entries)
        
        return f'''import {{ Tabs }} from 'expo-router';
import React from 'react';
import {{ HapticTab }} from '@/components/haptic-tab';
import {{ IconSymbol }} from '@/components/ui/icon-symbol';
import {{ Colors }} from '@/constants/theme';
import {{ useColorScheme }} from '@/hooks/use-color-scheme';

export default function TabLayout() {{
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{{{
        tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
        headerShown: false,
        tabBarButton: HapticTab,
      }}}}>
{tabs_content}
    </Tabs>
  );
}}
'''
    
    def _generate_welcome_modal(self) -> str:
        """Generate a welcome screen for modal.tsx with image and code example"""
        return '''import { StyleSheet, ScrollView, Image, Platform } from 'react-native';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';

export default function WelcomeModal() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Welcome Header */}
      <ThemedView style={styles.header}>
        <ThemedText type="title" style={styles.title}>
          Welcome! 👋
        </ThemedText>
        <ThemedText type="subtitle" style={styles.subtitle}>
          Your app is ready to use
        </ThemedText>
      </ThemedView>

      {/* App Preview Image */}
      <ThemedView style={styles.imageContainer}>
        <ThemedView style={styles.imagePlaceholder}>
          <ThemedText style={styles.imageText}>📱</ThemedText>
          <ThemedText style={styles.imageLabel}>App Preview</ThemedText>
        </ThemedView>
      </ThemedView>

      {/* Quick Start Guide */}
      <ThemedView style={styles.card}>
        <ThemedText type="subtitle" style={styles.cardTitle}>
          Quick Start Guide
        </ThemedText>
        <ThemedView style={styles.stepContainer}>
          <ThemedText style={styles.step}>1️⃣ Explore the tabs below</ThemedText>
          <ThemedText style={styles.step}>2️⃣ Edit screens in app/(tabs)/</ThemedText>
          <ThemedText style={styles.step}>3️⃣ Customize components</ThemedText>
          <ThemedText style={styles.step}>4️⃣ Build your features</ThemedText>
        </ThemedView>
      </ThemedView>

      {/* Code Example */}
      <ThemedView style={styles.card}>
        <ThemedText type="subtitle" style={styles.cardTitle}>
          Code Example 💻
        </ThemedText>
        <ThemedView style={styles.codeBlock}>
          <ThemedText style={styles.code}>
            {`// Edit app/(tabs)/index.tsx\\n\\nexport default function Home() {\\n  return (\\n    <ThemedView>\\n      <ThemedText>Hello!</ThemedText>\\n    </ThemedView>\\n  );\\n}`}
          </ThemedText>
        </ThemedView>
      </ThemedView>

      {/* Developer Tools */}
      <ThemedView style={styles.footer}>
        <ThemedText type="defaultSemiBold" style={styles.footerTitle}>
          Developer Tools
        </ThemedText>
        <ThemedText style={styles.footerText}>
          Press{' '}
          <ThemedText type="defaultSemiBold">
            {Platform.select({
              ios: 'Cmd + D',
              android: 'Cmd + M',
              web: 'F12',
            })}
          </ThemedText>
          {' '}to open dev menu
        </ThemedText>
      </ThemedView>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
    paddingTop: 20,
  },
  title: {
    marginBottom: 8,
  },
  subtitle: {
    opacity: 0.7,
  },
  imageContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  imagePlaceholder: {
    width: 200,
    height: 200,
    backgroundColor: '#f0f0f0',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderStyle: 'dashed',
  },
  imageText: {
    fontSize: 64,
    marginBottom: 8,
  },
  imageLabel: {
    fontSize: 14,
    opacity: 0.6,
  },
  card: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  cardTitle: {
    marginBottom: 12,
  },
  stepContainer: {
    gap: 8,
  },
  step: {
    fontSize: 15,
    lineHeight: 24,
  },
  codeBlock: {
    backgroundColor: '#1e1e1e',
    borderRadius: 8,
    padding: 12,
  },
  code: {
    fontFamily: Platform.select({
      ios: 'Menlo',
      android: 'monospace',
      default: 'monospace',
    }),
    fontSize: 12,
    color: '#d4d4d4',
    lineHeight: 18,
  },
  footer: {
    alignItems: 'center',
    marginTop: 8,
    padding: 16,
  },
  footerTitle: {
    marginBottom: 8,
  },
  footerText: {
    textAlign: 'center',
    opacity: 0.7,
  },
});
'''
