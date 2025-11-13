"""
Test script to verify Cloud Storage project listing
"""
import asyncio
import requests
import json

# Backend URL
BACKEND_URL = "https://mobile-generator-backend-1098053868371.us-central1.run.app"

async def test_list_projects():
    """Test the /projects endpoint"""
    print("=" * 80)
    print("Testing /projects endpoint")
    print("=" * 80)
    print()
    
    try:
        response = requests.get(f"{BACKEND_URL}/projects")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success!")
            print()
            print(f"📊 Total Projects: {data.get('total', 0)}")
            print(f"📁 Local Projects: {data.get('local_count', 0)}")
            print(f"☁️  Cloud Projects: {data.get('cloud_count', 0)}")
            print()
            
            if data.get('projects'):
                print("📋 Projects List:")
                print()
                for idx, project in enumerate(data['projects'], 1):
                    print(f"{idx}. {project['id'][:20]}...")
                    print(f"   Status: {project['status']}")
                    print(f"   Source: {project.get('source', 'unknown')}")
                    print(f"   Created: {project['created_at'][:19]}")
                    print(f"   Active: {project['is_active']}")
                    print()
            else:
                print("No projects found")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Exception: {e}")

async def test_health():
    """Test the /health endpoint"""
    print("=" * 80)
    print("Testing /health endpoint")
    print("=" * 80)
    print()
    
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"📊 Active Projects: {data['active_projects']}")
            print(f"💻 CPU: {data['system_metrics']['cpu_percent']}%")
            print(f"💾 Memory: {data['system_metrics']['memory_percent']}%")
            print(f"💿 Disk: {data['system_metrics']['disk_percent']}%")
        else:
            print(f"❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print()

async def main():
    """Run all tests"""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "CLOUD STORAGE PROJECT LISTING TEST" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    await test_health()
    await test_list_projects()
    
    print("=" * 80)
    print("✅ Testing Complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
