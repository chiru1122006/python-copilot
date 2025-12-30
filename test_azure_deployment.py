"""
Azure Deployment Testing Script
Tests all major endpoints after deployment
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://agentic-careerai.azurewebsites.net"
# For local testing, use: BASE_URL = "http://localhost:5000"

def print_test_result(test_name, success, response_data=None, error=None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} - {test_name}")
    if response_data:
        print(f"Response: {json.dumps(response_data, indent=2)}")
    if error:
        print(f"Error: {error}")
    print("-" * 60)

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        success = response.status_code == 200
        data = response.json() if response.ok else None
        print_test_result("Health Check", success, data)
        return success
    except Exception as e:
        print_test_result("Health Check", False, error=str(e))
        return False

def test_api_health():
    """Test API health check"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        success = response.status_code == 200
        data = response.json() if response.ok else None
        print_test_result("API Health Check", success, data)
        return success
    except Exception as e:
        print_test_result("API Health Check", False, error=str(e))
        return False

def test_embedding_generation():
    """Test embedding generation"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/embed",
            json={"text": "Hello, this is a test"},
            timeout=30
        )
        success = response.status_code == 200
        data = response.json() if response.ok else None
        if data and 'embedding' in data:
            # Don't print full embedding, just metadata
            data = {
                "status": data.get("status"),
                "dimension": data.get("dimension"),
                "embedding_preview": str(data.get("embedding", [])[:5]) + "..."
            }
        print_test_result("Embedding Generation", success, data)
        return success
    except Exception as e:
        print_test_result("Embedding Generation", False, error=str(e))
        return False

def test_reasoning_analyze():
    """Test reasoning agent"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/reasoning/analyze",
            json={
                "profile": {
                    "name": "Test User",
                    "current_level": "intermediate",
                    "skills": ["Python", "JavaScript"]
                }
            },
            timeout=30
        )
        success = response.status_code == 200
        data = response.json() if response.ok else None
        print_test_result("Reasoning Agent", success, data)
        return success
    except Exception as e:
        print_test_result("Reasoning Agent", False, error=str(e))
        return False

def test_skill_requirements():
    """Test skill gap agent"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/skills/requirements",
            json={"role": "Software Developer"},
            timeout=30
        )
        success = response.status_code == 200
        data = response.json() if response.ok else None
        print_test_result("Skill Requirements", success, data)
        return success
    except Exception as e:
        print_test_result("Skill Requirements", False, error=str(e))
        return False

def test_database_connection():
    """Test if database connection works (indirectly)"""
    # This tests if the app can connect to database
    # We'll use a simple endpoint that requires DB
    try:
        response = requests.get(
            f"{BASE_URL}/api/agent/state/1",
            timeout=30
        )
        # Even if user doesn't exist, if DB is connected, we'll get a proper response
        success = response.status_code in [200, 404]
        data = response.json() if response.ok else None
        print_test_result("Database Connection", success, data)
        return success
    except Exception as e:
        print_test_result("Database Connection", False, error=str(e))
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print(f"🧪 AZURE DEPLOYMENT TESTING")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("API Health", test_api_health),
        ("Embedding Generation", test_embedding_generation),
        ("Reasoning Agent", test_reasoning_analyze),
        ("Skill Requirements", test_skill_requirements),
        ("Database Connection", test_database_connection),
    ]
    
    results = []
    for name, test_func in tests:
        results.append((name, test_func()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Deployment is successful!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above for details.")
    
    print("=" * 60)

if __name__ == "__main__":
    print("\nStarting deployment tests...")
    print("This may take 30-60 seconds...\n")
    
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
