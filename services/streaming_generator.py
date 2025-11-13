"""
Streaming Generator Service
Real-time progressive app generation with WebSocket updates
"""
import asyncio
import logging
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class GenerationStage(str, Enum):
    """Stages of app generation"""
    ANALYZING = "analyzing"
    CREATING_PROJECT = "creating_project"
    GENERATING_BASE = "generating_base"
    INSTALLING_DEPS = "installing_deps"
    STARTING_SERVER = "starting_server"
    CREATING_TUNNEL = "creating_tunnel"
    PREVIEW_READY = "preview_ready"
    GENERATING_SCREENS = "generating_screens"
    ADDING_COMPONENTS = "adding_components"
    GENERATING_IMAGES = "generating_images"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ProgressUpdate:
    """Progress update message"""
    stage: GenerationStage
    message: str
    progress: int  # 0-100
    preview_url: Optional[str] = None
    screens_added: List[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "stage": self.stage.value,
            "message": self.message,
            "progress": self.progress,
            "preview_url": self.preview_url,
            "screens_added": self.screens_added or [],
            "error": self.error
        }


class StreamingGenerator:
    """
    Generates apps progressively with real-time updates
    
    Strategy:
    1. Create minimal working app immediately (10%)
    2. Start server and show preview ASAP (40%)
    3. Generate and add screens progressively (70%)
    4. Add components and polish (90%)
    5. Generate images in background (100%)
    """
    
    def __init__(
        self,
        code_generator,
        screen_generator,
        project_manager,
        command_executor,
        tunnel_manager
    ):
        """Initialize with service dependencies"""
        self.code_generator = code_generator
        self.screen_generator = screen_generator
        self.project_manager = project_manager
        self.command_executor = command_executor
        self.tunnel_manager = tunnel_manager
        
    async def generate_with_streaming(
        self,
        prompt: str,
        user_id: str,
        project_id: str,
        progress_callback: Callable[[ProgressUpdate], None],
        skip_screens: bool = False
    ) -> Dict:
        """
        Generate app with real-time progress updates
        
        Args:
            prompt: User's app description
            user_id: User identifier
            project_id: Project ID
            progress_callback: Function to call with progress updates
            
        Returns:
            Final result dictionary
        """
        try:
            # Stage 1: Quick analysis (5%)
            await self._send_progress(
                progress_callback,
                GenerationStage.ANALYZING,
                "Analyzing your app requirements...",
                5
            )
            
            # Generate app name quickly (don't wait for AI)
            import random
            import string
            import re
            
            # Extract keywords from prompt for app name
            words = re.findall(r'\b[a-z]{3,}\b', prompt.lower())
            if words:
                base_name = words[0][:10]
            else:
                base_name = "myapp"
            
            app_name = base_name
            
            # Analyze screens in background (simplified)
            screen_suggestions = {
                "total_screens": 4,
                "screens": ["Home", "Profile", "Settings", "About"]
            }
            
            # Stage 2: Create project structure (15%)
            await self._send_progress(
                progress_callback,
                GenerationStage.CREATING_PROJECT,
                f"Creating {app_name} project...",
                15
            )
            
            project = self.project_manager.create_project(user_id, prompt)
            
            # Create Expo project with minimal template
            import os
            import random
            import string
            
            unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            full_app_name = f"{app_name}{unique_suffix}"
            
            parent_dir = os.path.dirname(project.directory)
            expo_project_dir = await self.command_executor.create_expo_project(
                parent_dir=parent_dir,
                app_name=full_app_name,
                timeout=180
            )
            project.directory = expo_project_dir
            
            # Stage 3: Generate minimal base code (25%)
            await self._send_progress(
                progress_callback,
                GenerationStage.GENERATING_BASE,
                "Generating base app structure...",
                25
            )
            
            # Generate only the essential home screen
            base_code = await self._generate_minimal_base(prompt)
            self.project_manager.write_code_files(project, base_code)
            
            # Stage 4: Install dependencies in parallel with tunnel prep (35%)
            await self._send_progress(
                progress_callback,
                GenerationStage.INSTALLING_DEPS,
                "Installing dependencies...",
                35
            )
            
            await self.command_executor.setup_expo_project(
                project_dir=project.directory,
                port=project.port,
                timeout=300
            )
            
            # Stage 5: Start server (45%)
            await self._send_progress(
                progress_callback,
                GenerationStage.STARTING_SERVER,
                "Starting development server...",
                45
            )
            
            expo_process = await self.command_executor.start_expo_server(
                project_dir=project.directory,
                port=project.port
            )
            
            # Stage 6: Create tunnel (55%)
            await self._send_progress(
                progress_callback,
                GenerationStage.CREATING_TUNNEL,
                "Creating preview link...",
                55
            )
            
            preview_url = await self.tunnel_manager.create_tunnel(
                port=project.port,
                project_id=project.id
            )
            
            self.project_manager.update_preview_url(project.id, preview_url)
            
            # Stage 7: PREVIEW READY! (60%)
            await self._send_progress(
                progress_callback,
                GenerationStage.PREVIEW_READY,
                "Preview ready! Generating additional screens...",
                60,
                preview_url=preview_url
            )
            
            # Stage 8: Generate screens progressively (60-85%)
            screens_added = []
            
            if not skip_screens and screen_suggestions.get('total_screens', 0) > 0:
                await self._send_progress(
                    progress_callback,
                    GenerationStage.GENERATING_SCREENS,
                    "Adding screens with dummy data...",
                    65
                )
                
                # Generate screens in batches
                screens_added = await self._generate_screens_progressively(
                    prompt,
                    project.directory,
                    screen_suggestions,
                    progress_callback
                )
            else:
                # Skip screen generation for faster preview
                await self._send_progress(
                    progress_callback,
                    GenerationStage.GENERATING_SCREENS,
                    "Skipping additional screens for faster preview...",
                    85
                )
            
            # Stage 9: Add components (90%)
            await self._send_progress(
                progress_callback,
                GenerationStage.ADDING_COMPONENTS,
                "Creating reusable components...",
                90,
                preview_url=preview_url,
                screens_added=screens_added
            )
            
            await self._add_common_components(project.directory)
            
            # Stage 10: Generate images in background (95%)
            await self._send_progress(
                progress_callback,
                GenerationStage.GENERATING_IMAGES,
                "Generating images (this continues in background)...",
                95,
                preview_url=preview_url,
                screens_added=screens_added
            )
            
            # Start image generation but don't wait
            asyncio.create_task(
                self._generate_images_background(
                    prompt,
                    project.directory,
                    progress_callback
                )
            )
            
            # Stage 11: Complete! (100%)
            await self._send_progress(
                progress_callback,
                GenerationStage.COMPLETE,
                "App generation complete!",
                100,
                preview_url=preview_url,
                screens_added=screens_added
            )
            
            return {
                "success": True,
                "project_id": project.id,
                "preview_url": preview_url,
                "screens_added": screens_added,
                "app_name": full_app_name
            }
            
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}", exc_info=True)
            await self._send_progress(
                progress_callback,
                GenerationStage.ERROR,
                f"Error: {str(e)}",
                0,
                error=str(e)
            )
            raise
    
    async def _send_progress(
        self,
        callback: Callable,
        stage: GenerationStage,
        message: str,
        progress: int,
        preview_url: Optional[str] = None,
        screens_added: Optional[List[str]] = None
    ):
        """Send progress update via callback"""
        update = ProgressUpdate(
            stage=stage,
            message=message,
            progress=progress,
            preview_url=preview_url,
            screens_added=screens_added
        )
        
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(update)
            else:
                callback(update)
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")
    
    async def _generate_minimal_base(self, prompt: str):
        """Generate minimal working app with just home screen"""
        # Skip AI generation for speed - use a template
        from services.code_generator import GeneratedCode, CodeFile
        
        # Create a minimal working home screen
        minimal_code = '''import { StyleSheet, ScrollView, View, Text } from 'react-native';

export default function HomeScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Welcome! 👋</Text>
        <Text style={styles.subtitle}>Your app is being generated...</Text>
      </View>
      
      <View style={styles.card}>
        <Text style={styles.cardTitle}>🚀 Getting Started</Text>
        <Text style={styles.cardText}>
          We're creating your custom screens and features.
          This preview will update automatically as we add more content.
        </Text>
      </View>
      
      <View style={styles.card}>
        <Text style={styles.cardTitle}>⚡ Real-Time Updates</Text>
        <Text style={styles.cardText}>
          Watch as new screens appear in the navigation.
          No need to refresh - everything updates live!
        </Text>
      </View>
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
    marginBottom: 30,
    paddingTop: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  card: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  cardText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#666',
  },
});
'''
        
        return GeneratedCode(
            files=[CodeFile(path="app/(tabs)/index.tsx", content=minimal_code)],
            dependencies=[],
            expo_version="50.0.0"
        )
    
    async def _generate_screens_progressively(
        self,
        prompt: str,
        project_dir: str,
        screen_suggestions: Dict,
        progress_callback: Callable
    ) -> List[str]:
        """Generate screens in batches with progress updates"""
        screens_added = []
        
        if not screen_suggestions or screen_suggestions.get('total_screens', 0) == 0:
            return screens_added
        
        # Generate screens
        screen_definitions = await self.screen_generator.analyze_and_generate_screens(
            prompt,
            generate_images=False  # Images come later
        )
        
        # Write screens in batches
        batch_size = 2
        total_screens = len(screen_definitions)
        
        for i in range(0, total_screens, batch_size):
            batch = screen_definitions[i:i + batch_size]
            
            # Write batch
            loop = asyncio.get_event_loop()
            created_files = await loop.run_in_executor(
                None,
                self.screen_generator.write_screens_to_project,
                batch,
                project_dir
            )
            
            screens_added.extend([s.name for s in batch])
            
            # Update progress (65-85%)
            progress = 65 + int((i + len(batch)) / total_screens * 20)
            await self._send_progress(
                progress_callback,
                GenerationStage.GENERATING_SCREENS,
                f"Added {len(screens_added)}/{total_screens} screens...",
                progress,
                screens_added=screens_added
            )
            
            # Small delay to allow hot reload
            await asyncio.sleep(0.5)
        
        return screens_added
    
    async def _add_common_components(self, project_dir: str):
        """Add common reusable components"""
        # Create components directory
        import os
        components_dir = os.path.join(project_dir, "components")
        os.makedirs(components_dir, exist_ok=True)
        
        # Add a simple card component
        card_component = '''import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export function Card({ children, style }: CardProps) {
  return (
    <View style={[styles.card, style]}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
});
'''
        
        card_path = os.path.join(components_dir, "Card.tsx")
        with open(card_path, 'w', encoding='utf-8') as f:
            f.write(card_component)
    
    async def _generate_images_background(
        self,
        prompt: str,
        project_dir: str,
        progress_callback: Callable
    ):
        """Generate images in background without blocking"""
        try:
            logger.info("Starting background image generation")
            
            # Analyze what images are needed
            image_requirements = await self.screen_generator._analyze_required_images(prompt)
            
            if not image_requirements:
                logger.info("No images to generate")
                return
            
            # Generate images one by one
            for i, img_req in enumerate(image_requirements):
                try:
                    await self.screen_generator._generate_single_image(
                        img_req,
                        project_dir
                    )
                    logger.info(f"Generated image {i+1}/{len(image_requirements)}: {img_req.filename}")
                except Exception as e:
                    logger.warning(f"Failed to generate image {img_req.filename}: {e}")
            
            logger.info("Background image generation complete")
            
        except Exception as e:
            logger.error(f"Background image generation failed: {e}")
