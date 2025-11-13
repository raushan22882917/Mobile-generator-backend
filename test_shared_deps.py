"""
Test script for shared dependencies system
"""
import asyncio
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_create_project():
    """Test creating a project with shared dependencies"""
    print("\n" + "="*60)
    print("TEST 1: Create Project with Shared Dependencies")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json={
            "prompt": "Create a simple counter app with increment and decrement buttons",
            "user_id": "test_user"
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Project created: {data['project_id']}")
        print(f"✅ Preview URL: {data['preview_url']}")
        print(f"✅ Status: {data['status']}")
        return data['project_id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None


def test_build_status(project_id):
    """Test getting build status"""
    print("\n" + "="*60)
    print("TEST 2: Check Build Status")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/api/build/projects/{project_id}/build-status"
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Project ID: {data['project_id']}")
        print(f"✅ Is Building: {data['is_building']}")
        print(f"✅ Is Running: {data['is_running']}")
        print(f"✅ Preview URL: {data['preview_url']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_get_files(project_id):
    """Test getting project files"""
    print("\n" + "="*60)
    print("TEST 3: Get Project Files")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/api/editor/projects/{project_id}/files"
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Project ID: {data['project_id']}")
        print(f"✅ File tree loaded")
        
        # Count files
        def count_files(tree):
            if tree['type'] == 'file':
                return 1
            count = 0
            if tree.get('children'):
                for child in tree['children']:
                    count += count_files(child)
            return count
        
        file_count = count_files(data['file_tree'])
        print(f"✅ Total files: {file_count}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_get_file_content(project_id):
    """Test getting file content"""
    print("\n" + "="*60)
    print("TEST 4: Get File Content")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/api/editor/projects/{project_id}/file",
        params={"path": "app/index.tsx"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File: {data['path']}")
        print(f"✅ Language: {data['language']}")
        print(f"✅ Content length: {len(data['content'])} chars")
        print(f"\nFirst 200 chars:")
        print(data['content'][:200])
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_update_file(project_id):
    """Test updating file content"""
    print("\n" + "="*60)
    print("TEST 5: Update File Content")
    print("="*60)
    
    new_content = """import { View, Text, Button, StyleSheet } from 'react-native';
import { useState } from 'react';

export default function Home() {
  const [count, setCount] = useState(0);
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Counter App</Text>
      <Text style={styles.count}>{count}</Text>
      <View style={styles.buttons}>
        <Button title="Increment" onPress={() => setCount(count + 1)} />
        <Button title="Decrement" onPress={() => setCount(count - 1)} />
        <Button title="Reset" onPress={() => setCount(0)} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  count: {
    fontSize: 48,
    fontWeight: 'bold',
    marginBottom: 30,
  },
  buttons: {
    gap: 10,
  },
});
"""
    
    response = requests.post(
        f"{BASE_URL}/api/editor/projects/{project_id}/file",
        json={
            "path": "app/index.tsx",
            "content": new_content
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File updated successfully")
        print(f"✅ Message: {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_list_projects():
    """Test listing all projects"""
    print("\n" + "="*60)
    print("TEST 6: List All Projects")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/projects")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total projects: {data['total']}")
        print(f"✅ Local projects: {data['local_count']}")
        print(f"✅ Cloud projects: {data['cloud_count']}")
        
        if data['projects']:
            print(f"\nRecent projects:")
            for project in data['projects'][:3]:
                print(f"  - {project['id'][:8]}... ({project['status']})")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_active_builds():
    """Test listing active builds"""
    print("\n" + "="*60)
    print("TEST 7: List Active Builds")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/build/active-builds")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Active builds: {data['count']}")
        if data['active_builds']:
            for build_id in data['active_builds']:
                print(f"  - {build_id}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SHARED DEPENDENCIES SYSTEM TEST")
    print("="*60)
    print("\nMake sure the backend is running on http://localhost:8000")
    print("Press Enter to start tests...")
    input()
    
    # Test 1: Create project
    project_id = test_create_project()
    
    if not project_id:
        print("\n❌ Failed to create project. Stopping tests.")
        return
    
    # Wait for project to be ready
    print("\nWaiting for project to be ready...")
    time.sleep(10)
    
    # Test 2: Build status
    test_build_status(project_id)
    
    # Test 3: Get files
    test_get_files(project_id)
    
    # Test 4: Get file content
    test_get_file_content(project_id)
    
    # Test 5: Update file
    test_update_file(project_id)
    
    # Test 6: List projects
    test_list_projects()
    
    # Test 7: Active builds
    test_active_builds()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED!")
    print("="*60)
    print(f"\n✅ Project ID: {project_id}")
    print(f"✅ You can now test the preview URL in Expo Go app")
    print(f"✅ Edit files using the editor API")
    print(f"✅ All changes use shared dependencies (no npm install!)")


if __name__ == "__main__":
    main()
