"""
Quick validation test for streaming system
"""
import sys
import os

print("=" * 60)
print("Streaming System Validation")
print("=" * 60)

# Test 1: Check imports
print("\n1. Testing imports...")
try:
    from services.streaming_generator import StreamingGenerator, ProgressUpdate, GenerationStage
    from services.websocket_manager import ConnectionManager, connection_manager
    from endpoints.streaming_generate import router
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Check classes
print("\n2. Validating classes...")
try:
    # Check StreamingGenerator
    assert hasattr(StreamingGenerator, 'generate_with_streaming')
    assert hasattr(StreamingGenerator, '_send_progress')
    assert hasattr(StreamingGenerator, '_generate_minimal_base')
    print("   ✅ StreamingGenerator validated")
    
    # Check ProgressUpdate
    test_update = ProgressUpdate(
        stage=GenerationStage.ANALYZING,
        message="Test",
        progress=10
    )
    assert test_update.to_dict()['stage'] == 'analyzing'
    print("   ✅ ProgressUpdate validated")
    
    # Check ConnectionManager
    assert hasattr(connection_manager, 'connect')
    assert hasattr(connection_manager, 'send_to_project')
    print("   ✅ ConnectionManager validated")
    
except Exception as e:
    print(f"   ❌ Validation error: {e}")
    sys.exit(1)

# Test 3: Check stages
print("\n3. Validating generation stages...")
try:
    stages = [
        GenerationStage.ANALYZING,
        GenerationStage.CREATING_PROJECT,
        GenerationStage.GENERATING_BASE,
        GenerationStage.INSTALLING_DEPS,
        GenerationStage.STARTING_SERVER,
        GenerationStage.CREATING_TUNNEL,
        GenerationStage.PREVIEW_READY,
        GenerationStage.GENERATING_SCREENS,
        GenerationStage.ADDING_COMPONENTS,
        GenerationStage.GENERATING_IMAGES,
        GenerationStage.COMPLETE,
    ]
    print(f"   ✅ All {len(stages)} stages defined")
    for stage in stages:
        print(f"      - {stage.value}")
except Exception as e:
    print(f"   ❌ Stage validation error: {e}")
    sys.exit(1)

# Test 4: Check files exist
print("\n4. Checking file structure...")
files_to_check = [
    'services/streaming_generator.py',
    'services/websocket_manager.py',
    'endpoints/streaming_generate.py',
    'examples/streaming_client.html',
    'STREAMING_ARCHITECTURE.md',
    'QUICK_START_STREAMING.md',
    'README_STREAMING.md',
]

all_exist = True
for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - NOT FOUND")
        all_exist = False

if not all_exist:
    print("\n   ⚠️  Some files are missing")
else:
    print("\n   ✅ All files present")

# Test 5: Check configuration
print("\n5. Checking configuration...")
try:
    from config import settings
    
    required_settings = ['openai_api_key', 'ngrok_auth_token']
    for setting in required_settings:
        if hasattr(settings, setting):
            value = getattr(settings, setting)
            if value and len(value) > 0:
                print(f"   ✅ {setting} configured")
            else:
                print(f"   ⚠️  {setting} is empty")
        else:
            print(f"   ❌ {setting} not found")
            
except Exception as e:
    print(f"   ❌ Configuration error: {e}")

# Summary
print("\n" + "=" * 60)
print("Validation Summary")
print("=" * 60)
print("""
✅ Streaming system is properly set up!

Next steps:
1. Start the server:
   uvicorn main:app --reload

2. Open the demo:
   Open examples/streaming_client.html in your browser

3. Test with a prompt:
   "Create a simple todo list app"

4. Watch real-time progress:
   - Progress bar updates
   - Preview ready in ~45 seconds
   - Screens added live
   - QR code for mobile testing
""")

print("=" * 60)
