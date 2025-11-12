"""
Parallel Workflow Service
Orchestrates parallel execution of ngrok tunnel creation and AI screen generation
"""
import asyncio
import logging
from typing import Dict, List
from dataclasses import dataclass

from services.screen_generator import ScreenGenerator, ScreenDefinition
from services.tunnel_manager import TunnelManager

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Result of parallel workflow execution"""
    preview_url: str
    screens_created: List[str]
    screen_definitions: List[ScreenDefinition]
    images_generated: Dict[str, str]
    success: bool
    error: str = None


class ParallelWorkflow:
    """
    Orchestrates parallel execution of:
    1. Ngrok tunnel creation for mobile preview
    2. AI-powered screen generation
    """
    
    def __init__(
        self,
        screen_generator: ScreenGenerator,
        tunnel_manager: TunnelManager
    ):
        """
        Initialize ParallelWorkflow
        
        Args:
            screen_generator: ScreenGenerator instance
            tunnel_manager: TunnelManager instance
        """
        self.screen_generator = screen_generator
        self.tunnel_manager = tunnel_manager
        logger.info("ParallelWorkflow initialized")
    
    async def execute(
        self,
        prompt: str,
        project_id: str,
        project_dir: str,
        port: int,
        generate_images: bool = True
    ) -> WorkflowResult:
        """
        Execute parallel workflow:
        - Create ngrok tunnel for live preview
        - Generate screens based on prompt using AI
        - Generate images for the app
        
        Args:
            prompt: User's app description
            project_id: Project identifier
            project_dir: Path to project directory
            port: Port number for Expo server
            generate_images: Whether to generate images (default: True)
            
        Returns:
            WorkflowResult with tunnel URL, created screens, and generated images
        """
        logger.info(f"Starting parallel workflow for project {project_id}")
        
        try:
            # Execute three tasks in parallel:
            # 1. Create tunnel
            # 2. Generate screens (which analyzes image needs)
            # 3. (Images will be generated after screens are analyzed)
            tunnel_task = self._create_tunnel(port, project_id)
            screens_task = self._generate_screens(prompt, project_dir, generate_images)
            
            # Wait for tunnel and screens
            tunnel_url, screen_definitions = await asyncio.gather(
                tunnel_task,
                screens_task
            )
            
            # Now generate images in parallel with writing screens
            write_task = asyncio.create_task(
                self._write_screens(screen_definitions, project_dir)
            )
            
            images_task = asyncio.create_task(
                self._generate_images(screen_definitions, project_dir, generate_images)
            )
            
            # Wait for both to complete
            created_files, generated_images = await asyncio.gather(
                write_task,
                images_task
            )
            
            logger.info(
                f"Parallel workflow completed: "
                f"tunnel={tunnel_url}, screens={len(created_files)}, "
                f"images={len(generated_images)}"
            )
            
            return WorkflowResult(
                preview_url=tunnel_url,
                screens_created=created_files,
                screen_definitions=screen_definitions,
                images_generated=generated_images,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Parallel workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                preview_url="",
                screens_created=[],
                screen_definitions=[],
                images_generated={},
                success=False,
                error=str(e)
            )
    
    async def _create_tunnel(self, port: int, project_id: str) -> str:
        """
        Create ngrok tunnel
        
        Args:
            port: Port number
            project_id: Project identifier
            
        Returns:
            Public tunnel URL
        """
        logger.info(f"Creating tunnel for port {port}")
        tunnel_url = await self.tunnel_manager.create_tunnel(port, project_id)
        logger.info(f"Tunnel created: {tunnel_url}")
        return tunnel_url
    
    async def _generate_screens(
        self,
        prompt: str,
        project_dir: str,
        generate_images: bool
    ) -> List[ScreenDefinition]:
        """
        Generate screens using AI
        
        Args:
            prompt: User's app description
            project_dir: Path to project directory
            generate_images: Whether to analyze image needs
            
        Returns:
            List of ScreenDefinition objects
        """
        logger.info("Generating screens with AI")
        screens = await self.screen_generator.analyze_and_generate_screens(
            prompt,
            generate_images=generate_images
        )
        logger.info(f"Generated {len(screens)} screen definitions")
        return screens
    
    async def _write_screens(
        self,
        screen_definitions: List[ScreenDefinition],
        project_dir: str
    ) -> List[str]:
        """
        Write screens to project directory
        
        Args:
            screen_definitions: List of ScreenDefinition objects
            project_dir: Path to project directory
            
        Returns:
            List of created file paths
        """
        logger.info("Writing screens to project")
        loop = asyncio.get_event_loop()
        created_files = await loop.run_in_executor(
            None,
            self.screen_generator.write_screens_to_project,
            screen_definitions,
            project_dir
        )
        return created_files
    
    async def _generate_images(
        self,
        screen_definitions: List[ScreenDefinition],
        project_dir: str,
        generate_images: bool
    ) -> Dict[str, str]:
        """
        Generate images for screens
        
        Args:
            screen_definitions: List of ScreenDefinition objects
            project_dir: Path to project directory
            generate_images: Whether to generate images
            
        Returns:
            Dictionary mapping filename to file path
        """
        if not generate_images:
            logger.info("Image generation disabled")
            return {}
        
        logger.info("Generating images for project")
        generated_images = await self.screen_generator.generate_images_for_project(
            screen_definitions,
            project_dir
        )
        return generated_images
