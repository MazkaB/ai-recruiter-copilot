#!/usr/bin/env python3
"""
Simple test script for AI Recruiter Co-Pilot API
Run this to test basic functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test basic API functionality"""
    
    print("🧪 Testing AI Recruiter Co-Pilot API")
    print("=" * 40)
    
    # Test 1: Check if server is running
    print("1. Testing server connection...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
        else:
            print("❌ Server connection failed")
            return False
    except Exception as e:
        print(f"❌ Server connection error: {str(e)}")
        return False
    
    # Test 2: Create session
    print("\n2. Testing session creation...")
    try:
        response = requests.post(f"{BASE_URL}/session/start")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get("session_id")
            print("✅ Session created successfully")
            print(f"   Session ID: {session_id}")
        else:
            print("❌ Session creation failed")
            return False
    except Exception as e:
        print(f"❌ Session creation error: {str(e)}")
        return False
    
    # Test 3: Check session status
    print("\n3. Testing session status...")
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Session status retrieved")
            print(f"   Status: {status_data.get('status')}")
        else:
            print("❌ Session status check failed")
    except Exception as e:
        print(f"❌ Session status error: {str(e)}")
    
    # Test 4: Test debug endpoint
    print("\n4. Testing debug endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}/debug")
        if response.status_code == 200:
            debug_data = response.json()
            print("✅ Debug info retrieved")
            print(f"   Questions: {debug_data.get('total_questions', 0)}")
            print(f"   Answers: {debug_data.get('answers_count', 0)}")
        else:
            print("❌ Debug endpoint failed")
    except Exception as e:
        print(f"❌ Debug endpoint error: {str(e)}")
    
    # Test 5: Test CV upload with dummy data
    print("\n5. Testing CV upload...")
    try:
        # Create a dummy text file
        dummy_cv = """
        John Doe
        Software Engineer
        john.doe@example.com
        
        Experience:
        - Senior Developer at Tech Corp (2020-2024)
        - Full-stack development with React and Python
        - Led team of 5 developers
        
        Skills: Python, JavaScript, React, Node.js, SQL
        
        Education:
        - BS Computer Science, University (2020)
        """
        
        files = {'file': ('test_cv.txt', dummy_cv, 'text/plain')}
        response = requests.post(f"{BASE_URL}/session/{session_id}/upload-cv", files=files)
        
        if response.status_code == 200:
            cv_data = response.json()
            print("✅ CV upload successful")
            print(f"   Questions generated: {cv_data.get('questions_generated', 0)}")
        else:
            print(f"❌ CV upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ CV upload error: {str(e)}")
    
    # Test 6: Get first question
    print("\n6. Testing question retrieval...")
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}/question")
        if response.status_code == 200:
            question_data = response.json()
            if question_data.get("status") == "interview_complete":
                print("✅ Interview marked as complete")
            else:
                print("✅ Question retrieved")
                print(f"   Question: {question_data.get('question', '')[:100]}...")
        else:
            print("❌ Question retrieval failed")
    except Exception as e:
        print(f"❌ Question retrieval error: {str(e)}")
    
    print("\n🎉 Basic API test completed!")
    print(f"Session ID for manual testing: {session_id}")
    print(f"Debug URL: {BASE_URL}/session/{session_id}/debug")
    
    return True

if __name__ == "__main__":
    test_api()