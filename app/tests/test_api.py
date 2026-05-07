#!/usr/bin/env python3
"""
AIService Test Script - Works on Windows, Mac, Linux

Save this as: test_api.py
Run with: python test_api.py
"""

import requests
import json
import sys

def test_api():
    """Test the AIService endpoint."""
    
    print("=" * 50)
    print("AIService Test Script")
    print("=" * 50)
    print()
    
    # Check if API is running
    print("Checking if API is running on http://localhost:8000...")
    try:
        health = requests.get("http://localhost:8000/", timeout=5)
        print("✓ API is running!")
    except requests.exceptions.ConnectionError:
        print("✗ API is not running!")
        print()
        print("Start your server first with:")
        print("  python -m uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error checking API: {e}")
        sys.exit(1)
    
    print()
    print("Sending test request...")
    print()
    
    # Prepare request
    url = "http://localhost:8000/graphs/"
    
    data = {
        "genome_properties": [
            {
                "property_type": "STANDARD",
                "name": "age",
                "value": "28",
                "unit": "years",
                "genome_type": "numeric"
            },
            {
                "property_type": "STANDARD",
                "name": "experience",
                "value": "5",
                "unit": "years",
                "genome_type": "numeric"
            }
        ]
    }
    
    # Make request
    try:
        response = requests.post(url, json=data, timeout=30)
        
        # Check response
        if response.status_code == 200:
            print("✓ Request successful!")
            print(f"Status Code: {response.status_code}")
            print()
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            print()
            print("✓ Everything is working!")
            return 0
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print()
            print("Response:")
            print(response.text)
            return 1
    
    except requests.exceptions.Timeout:
        print("✗ Request timed out!")
        print()
        print("The API is slow or not responding.")
        print("Check:")
        print("1. Is your API running?")
        print("2. Is GEMINI_API_KEY set correctly?")
        print("3. Check the API terminal for errors")
        return 1
    
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed!")
        print()
        print("Can't connect to API.")
        print("Make sure it's running with:")
        print("  python -m uvicorn app.main:app --reload")
        return 1
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_api())
