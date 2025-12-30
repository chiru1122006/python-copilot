"""Quick API test script"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    print("Testing health endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_resume():
    print("\nTesting resume generation...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/resume/generate",
            json={"user_id": 1, "target_role": "Software Engineer"},
            timeout=120
        )
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Response keys: {data.keys() if isinstance(data, dict) else 'not a dict'}")
        if 'error' in data:
            print(f"Error: {data['error']}")
        else:
            print(f"Success: {data.get('message', 'OK')}")
            if 'resume_data' in data:
                print(f"Resume data keys: {data['resume_data'].keys()}")
        return True
    except requests.exceptions.Timeout:
        print("Request timed out - LLM call may be slow")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if test_health():
        print("\n✓ Server is healthy!")
        test_resume()
    else:
        print("\n✗ Server not responding - make sure app.py is running")
