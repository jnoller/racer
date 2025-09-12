#!/usr/bin/env python3
"""
Test script for the new rerun functionality.
"""

import requests
import json
import subprocess
import os

def test_rerun_api():
    """Test the rerun API endpoint."""
    print("Testing Rerun API...")
    
    # Test POST /project/rerun with non-existent project
    print("\n1. Testing POST /project/rerun")
    response = requests.post("http://localhost:8000/project/rerun", 
                           json={"project_id": "fake-project-id"})
    if response.status_code == 200:
        data = response.json()
        print(f"✓ POST /project/rerun working: {data['message']}")
        print(f"  Success: {data['success']}")
    else:
        print(f"✗ POST /project/rerun failed: {response.status_code} - {response.text}")
        return False
    
    return True

def test_rerun_cli():
    """Test the rerun CLI command."""
    print("\nTesting Rerun CLI Commands...")
    
    try:
        # Test rerun command with no projects
        print("\n1. Testing 'racer rerun'")
        result = subprocess.run(["racer", "rerun"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✓ rerun command working")
            print(f"Output: {result.stdout.strip()}")
        else:
            print(f"✗ rerun command failed: {result.stderr}")
            return False
        
        # Test rerun with --list flag
        print("\n2. Testing 'racer rerun --list'")
        result = subprocess.run(["racer", "rerun", "--list"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✓ rerun --list command working")
            print(f"Output: {result.stdout.strip()}")
        else:
            print(f"✗ rerun --list command failed: {result.stderr}")
            return False
        
        # Test rerun with fake project ID
        print("\n3. Testing 'racer rerun --project-id fake-id'")
        result = subprocess.run(["racer", "rerun", "--project-id", "fake-id"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✓ rerun with project-id working")
            print(f"Output: {result.stdout.strip()}")
        else:
            print(f"✗ rerun with project-id failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False

def test_help_commands():
    """Test that help commands show the new rerun command."""
    print("\nTesting Help Commands...")
    
    try:
        # Test main help
        result = subprocess.run(["racer", "--help"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0 and "rerun" in result.stdout:
            print("✓ Main help shows rerun command")
        else:
            print("✗ Main help missing rerun command")
            return False
        
        # Test rerun help
        result = subprocess.run(["racer", "rerun", "--help"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0 and "Project ID to rerun" in result.stdout:
            print("✓ Rerun help shows correct options")
        else:
            print("✗ Rerun help missing expected options")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Help test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Racer Rerun Functionality")
    print("=" * 50)
    
    # Test API endpoint
    api_ok = test_rerun_api()
    
    # Test CLI commands
    cli_ok = test_rerun_cli()
    
    # Test help commands
    help_ok = test_help_commands()
    
    print("\n" + "=" * 50)
    if api_ok and cli_ok and help_ok:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
