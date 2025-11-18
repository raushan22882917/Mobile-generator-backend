"""
Backend Test Script
Tests the backend API and verifies app generation sequence
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional

# Backend URL
BASE_URL = "https://mobile-generator-backend-1098053868371.us-central1.run.app"
API_BASE = f"{BASE_URL}/api/v1"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_info(msg: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.RESET}")


def test_root_endpoint() -> bool:
    """Test the root endpoint"""
    print_section("Test 1: Root Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Root endpoint responded (Status: {response.status_code})")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify expected fields
            if "message" in data and "version" in data and "status" in data:
                print_success("Response contains expected fields")
                return True
            else:
                print_error("Response missing expected fields")
                return False
        else:
            print_error(f"Root endpoint failed (Status: {response.status_code})")
            print_info(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Root endpoint test failed: {str(e)}")
        return False


def test_health_endpoint() -> bool:
    """Test health endpoint if available"""
    print_section("Test 2: Health Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health endpoint responded (Status: {response.status_code})")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_info(f"Health endpoint not available or returned {response.status_code}")
            return True  # Not critical
            
    except Exception as e:
        print_info(f"Health endpoint not available: {str(e)}")
        return True  # Not critical


def test_project_status(project_id: str) -> Dict[str, Any]:
    """Test project status endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/project-status/{project_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                return {
                    "error": f"Failed to parse JSON response: {str(e)}",
                    "text": response.text[:200] if response.text else "Empty response"
                }
        else:
            error_text = response.text[:200] if response.text else "No error message"
            return {
                "error": f"HTTP {response.status_code}: {error_text}",
                "status_code": response.status_code
            }
    except requests.exceptions.Timeout:
        return {"error": "Request timeout after 10 seconds"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        return {"error": f"Unexpected error: {error_msg}"}


def test_fast_generate() -> Optional[str]:
    """Test fast generate endpoint"""
    print_section("Test 3: Fast Generate Endpoint")
    
    test_prompt = "Create a simple todo app with a list of tasks and add task functionality"
    
    try:
        # Try without API key first (may not require auth)
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "prompt": test_prompt,
            "user_id": "test_user",
            "template_id": None
        }
        
        print_info(f"Sending generation request...")
        print_info(f"Prompt: {test_prompt[:50]}...")
        
        response = requests.post(
            f"{API_BASE}/fast-generate",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Fast generate endpoint responded (Status: {response.status_code})")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            if "project_id" in data:
                project_id = data["project_id"]
                print_success(f"Project ID: {project_id}")
                return project_id
            else:
                print_error("Response missing project_id")
                return None
                
        elif response.status_code == 401:
            print_info("Authentication required (expected). Trying with API key...")
            # Try with API key in header if provided
            api_key = input("Enter API key (or press Enter to skip): ").strip()
            if api_key:
                headers["X-API-Key"] = api_key
                response = requests.post(
                    f"{API_BASE}/fast-generate",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    print_success(f"Fast generate with API key successful")
                    print_info(f"Response: {json.dumps(data, indent=2)}")
                    if "project_id" in data:
                        return data["project_id"]
                else:
                    print_error(f"Fast generate with API key failed: {response.status_code}")
                    print_info(f"Response: {response.text}")
            else:
                print_info("Skipping fast generate test (auth required)")
            return None
        else:
            print_error(f"Fast generate endpoint failed (Status: {response.status_code})")
            print_info(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Fast generate test failed: {str(e)}")
        return None


def test_generate_stream() -> Optional[str]:
    """Test generate stream endpoint"""
    print_section("Test 4: Generate Stream Endpoint")
    
    test_prompt = "Create a simple calculator app with basic arithmetic operations"
    
    try:
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "prompt": test_prompt,
            "user_id": "test_user",
            "template_id": None,
            "fast_mode": True
        }
        
        print_info(f"Sending stream generation request...")
        print_info(f"Prompt: {test_prompt[:50]}...")
        
        response = requests.post(
            f"{API_BASE}/generate-stream",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Generate stream endpoint responded (Status: {response.status_code})")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            if "project_id" in data:
                project_id = data["project_id"]
                print_success(f"Project ID: {project_id}")
                print_info(f"WebSocket URL: {data.get('websocket_url', 'N/A')}")
                return project_id
            else:
                print_error("Response missing project_id")
                return None
                
        elif response.status_code == 401:
            print_info("Authentication required (expected). Skipping...")
            return None
        else:
            print_error(f"Generate stream endpoint failed (Status: {response.status_code})")
            print_info(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Generate stream test failed: {str(e)}")
        return None


def monitor_project_generation(project_id: str, max_wait: int = 120) -> bool:
    """Monitor project generation status"""
    print_section(f"Test 5: Monitor Project Generation - {project_id}")
    
    print_info(f"Monitoring project for up to {max_wait} seconds...")
    
    start_time = time.time()
    check_interval = 3  # Check every 3 seconds
    last_status = None
    status_changes = []
    
    while time.time() - start_time < max_wait:
        status_data = test_project_status(project_id)
        
        # Check if this is an HTTP/connection error (error key in our wrapper)
        if "error" in status_data and "status" not in status_data:
            # This is an HTTP error, not a project error
            print_error(f"Error checking status: {status_data['error']}")
            time.sleep(check_interval)
            continue
        
        # Extract project status information
        current_status = status_data.get("status", "unknown")
        exists = status_data.get("exists", False)
        project_error = status_data.get("error")  # Project error message (not HTTP error)
        
        # Track status changes
        if current_status != last_status:
            status_changes.append({
                "time": time.time() - start_time,
                "status": current_status
            })
            last_status = current_status
            
            elapsed = int(time.time() - start_time)
            print_info(f"[{elapsed}s] Status: {current_status}")
            
            if status_data.get("preview_url"):
                print_success(f"Preview URL: {status_data['preview_url']}")
            
            if project_error:
                # Truncate long error messages
                error_display = project_error[:150] + "..." if len(project_error) > 150 else project_error
                print_error(f"Project Error: {error_display}")
        
        # Also print periodic updates even if status hasn't changed (every 15 seconds)
        elapsed_seconds = int(time.time() - start_time)
        if elapsed_seconds > 0 and elapsed_seconds % 15 == 0:
            # Check if we already printed an update at this interval
            recent_updates = [int(s["time"]) for s in status_changes[-3:]]
            if elapsed_seconds not in recent_updates:
                print_info(f"[{elapsed_seconds}s] Still {current_status}... (waiting for progress)")
        
        # Check if generation is complete
        if exists and current_status == "ready":
            print_success(f"Project generation completed successfully!")
            if status_data.get("preview_url"):
                print_success(f"Preview URL: {status_data['preview_url']}")
            
            # Print status sequence
            print_info("\nStatus Sequence:")
            for change in status_changes:
                print_info(f"  [{change['time']:.1f}s] → {change['status']}")
            
            return True
        
        # Check if generation failed
        if exists and current_status in ["failed", "error"]:
            print_error(f"Project generation failed with status: {current_status}")
            if project_error:
                error_display = project_error[:200] + "..." if len(project_error) > 200 else project_error
                print_error(f"Error details: {error_display}")
            
            # Print status sequence
            if status_changes:
                print_info("\nStatus Sequence Before Failure:")
                for change in status_changes:
                    print_info(f"  [{change['time']:.1f}s] → {change['status']}")
            return False
        
        time.sleep(check_interval)
    
    print_error(f"Timeout waiting for project generation (waited {max_wait}s)")
    print_info(f"Final status: {last_status}")
    return False


def test_quick_status(project_id: str) -> bool:
    """Test quick status endpoint"""
    print_section("Test 6: Quick Status Endpoint")
    
    try:
        response = requests.get(
            f"{BASE_URL}/quick-status/{project_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Quick status endpoint responded")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_info(f"Quick status returned {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Quick status test failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("Backend API Test Suite")
    print("Testing: https://mobile-generator-backend-1098053868371.us-central1.run.app")
    print("="*60)
    print(Colors.RESET)
    
    results = {}
    
    # Test 1: Root endpoint
    results["root"] = test_root_endpoint()
    
    # Test 2: Health endpoint
    results["health"] = test_health_endpoint()
    
    # Test 3: Fast generate
    project_id = test_fast_generate()
    results["fast_generate"] = project_id is not None
    
    # Test 4: Generate stream (alternative endpoint)
    if not project_id:
        project_id = test_generate_stream()
        results["generate_stream"] = project_id is not None
    
    # Test 5: Monitor generation (if we have a project_id)
    if project_id:
        # Test quick status first
        test_quick_status(project_id)
        
        # Monitor generation
        results["generation_sequence"] = monitor_project_generation(project_id)
    else:
        print_info("Skipping generation monitoring (no project_id available)")
        results["generation_sequence"] = False
    
    # Summary
    print_section("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print_info(f"Tests passed: {passed_tests}/{total_tests}")
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    # Exit with appropriate code
    if passed_tests == total_tests:
        print_success("All tests passed!")
        sys.exit(0)
    else:
        print_error("Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

