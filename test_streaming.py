"""
Test script for streaming generation
"""
import asyncio
import json
from services.streaming_generator import StreamingGenerator, ProgressUpdate
from services.code_generator import CodeGenerator
from services.screen_generator import ScreenGenerator
from services.project_manager import ProjectManager
from services.command_executor import CommandExecutor
from services.tunnel_manager import TunnelManager
from config import settings


async def progress_callback(update: ProgressUpdate):
    """Print progress updates"""
    print(f"\n[{update.progress}%] {update.stage}")
    print(f"    {update.message}")
    if update.preview_url:
        print(f"    🎉 Preview: {update.preview_url}")
    if update.screens_added:
        print(f"    📱 Screens: {', '.join(update.screens_added)}")


async def test_streaming():
    """Test the streaming generation"""
    print("=" * 60)
    print("Testing Streaming App Generation")
    print("=" * 60)
    
    # Initialize services
    print("\n1. Initializing services...")
    
    code_generator = CodeGenerator(
        api_key=settings.openai_api_key,
        model="gpt-4",
        timeout=900
    )
    
    screen_generator = ScreenGenerator(
        api_key=settings.openai_api_key,
        model="gpt-4",
        gemini_api_key=getattr(settings, 'gemini_api_key', None)
    )
    
    project_manager = ProjectManager(
        base_dir=settings.projects_base_dir,
        max_concurrent_projects=settings.max_concurrent_projects
    )
    
    command_executor = CommandExecutor(default_timeout=300)
    
    tunnel_manager = TunnelManager(
        auth_token=settings.ngrok_auth_token,
        max_retries=3,
        retry_delay=5
    )
    
    # Create streaming generator
    streaming_gen = StreamingGenerator(
        code_generator=code_generator,
        screen_generator=screen_generator,
        project_manager=project_manager,
        command_executor=command_executor,
        tunnel_manager=tunnel_manager
    )
    
    print("✅ Services initialized")
    
    # Test prompt
    prompt = """
    Create a simple todo list app with the following features:
    - Home screen showing list of todos
    - Add new todo functionality
    - Mark todos as complete
    - Delete todos
    - Simple and clean UI
    """
    
    print(f"\n2. Testing with prompt:")
    print(f"   '{prompt.strip()[:100]}...'")
    
    # Generate with streaming
    print("\n3. Starting generation...\n")
    
    try:
        result = await streaming_gen.generate_with_streaming(
            prompt=prompt,
            user_id="test-user",
            project_id="test-project-001",
            progress_callback=progress_callback
        )
        
        print("\n" + "=" * 60)
        print("✅ GENERATION COMPLETE!")
        print("=" * 60)
        print(f"\nProject ID: {result['project_id']}")
        print(f"Preview URL: {result['preview_url']}")
        print(f"App Name: {result['app_name']}")
        print(f"Screens Added: {len(result['screens_added'])}")
        for screen in result['screens_added']:
            print(f"  - {screen}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n4. Cleaning up...")
        await tunnel_manager.close_all_tunnels()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    print("\n🚀 Starting Streaming Generation Test\n")
    asyncio.run(test_streaming())
    print("\n✅ Test completed!\n")
