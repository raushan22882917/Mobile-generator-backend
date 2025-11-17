"""
Initialize Global Shared Dependencies
Run this once to set up the global node_modules
"""
import asyncio
import logging
from services.shared_dependencies import SharedDependenciesManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Initialize global shared dependencies"""
    print("\n" + "="*60)
    print("INITIALIZING GLOBAL SHARED DEPENDENCIES")
    print("="*60)
    print("\nThis will install all Expo & React Native packages globally:")
    print("\n📦 Core Packages:")
    print("  - Expo ~51.0.0")
    print("  - React 18.2.0")
    print("  - React Native 0.74.5")
    print("\n🎭 Icons & UI Libraries:")
    print("  - @expo/vector-icons (15,000+ icons)")
    print("  - React Native Paper (Material Design 3)")
    print("  - React Native Elements (UI Toolkit)")
    print("  - NativeBase (Customizable components)")
    print("  - Tamagui (Lightweight UI)")
    print("  - Dripsy (Responsive design)")
    print("\n🎨 Styling & Theming:")
    print("  - NativeWind (Tailwind CSS)")
    print("  - Styled Components (CSS-in-JS)")
    print("  - Linear Gradient")
    print("\n💫 Animations:")
    print("  - Moti (Easy animations)")
    print("  - Lottie (Vector animations)")
    print("  - React Native Skia (Advanced graphics)")
    print("\n🧭 Navigation:")
    print("  - Expo Router")
    print("  - React Navigation (Stack, Tabs, Drawer)")
    print("  - Gesture Handler & Reanimated")
    print("\n📝 Forms & Validation:")
    print("  - React Hook Form")
    print("  - Formik")
    print("  - Yup")
    print("\n💾 Storage & API:")
    print("  - AsyncStorage, SecureStore")
    print("  - Axios")
    print("\n📸 Media & Images:")
    print("  - Expo Image, Camera, Image Picker")
    print("  - Fast Image (caching)")
    print("\n🎯 UX Enhancers:")
    print("  - Toast Messages")
    print("  - Modals & Bottom Sheets")
    print("  - Haptic Feedback")
    print("  - Blur Effects")
    print("\n🛠️ Utilities:")
    print("  - Location, Notifications, Sensors")
    print("  - Date-fns, Lodash, UUID")
    print("  - State Management (Zustand, Jotai)")
    print("\n...and 100+ more packages!")
    print("\nLocation: /tmp/shared_node_modules/global/")
    print("Time: ~5-10 minutes (one-time setup)")
    print("\nAll projects will use these via NODE_PATH.")
    print("\nPress Enter to continue...")
    input()
    
    # Create shared dependencies manager
    manager = SharedDependenciesManager()
    
    # Install global modules
    try:
        global_path = await manager.ensure_global_modules_installed()
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"\nGlobal node_modules installed at:")
        print(f"  {global_path}")
        print(f"\nAll projects will now use these dependencies.")
        print(f"No more npm install per project!")
        print("\n" + "="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ FAILED!")
        print("="*60)
        print(f"\nError: {e}")
        print("\nPlease check:")
        print("  1. Node.js and npm are installed")
        print("  2. You have internet connection")
        print("  3. You have write permissions to /tmp")
        print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
