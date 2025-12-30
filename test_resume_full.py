"""
Complete Resume Generation Test
Tests the end-to-end resume generation with PDF output
"""
import requests
import json
import os

BASE_URL = "http://127.0.0.1:5000"

def test_full_resume_generation():
    print("=" * 60)
    print("FULL RESUME GENERATION TEST")
    print("=" * 60)
    
    # Test 1: Generate resume
    print("\n1. Generating resume...")
    response = requests.post(
        f"{BASE_URL}/api/resume/generate",
        json={
            "user_id": 1,
            "target_role": "Full Stack Developer",
            "target_company": "Google",
            "job_description": "Looking for a Full Stack Developer with React and Node.js experience. Must have strong problem-solving skills."
        },
        timeout=120
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   Error: {response.text}")
        return False
    
    data = response.json()
    print(f"   Response status: {data.get('status')}")
    
    # Check resume data structure
    resume_data = data.get('resume_data', {})
    print(f"\n2. Resume Data Structure:")
    print(f"   - header: {list(resume_data.get('header', {}).keys())}")
    print(f"   - contact: {list(resume_data.get('contact', {}).keys())}")
    print(f"   - summary: {len(resume_data.get('summary', ''))} characters")
    print(f"   - skills: {len(resume_data.get('skills', []))} items")
    print(f"   - experience: {len(resume_data.get('experience', []))} items")
    print(f"   - education: {len(resume_data.get('education', []))} items")
    print(f"   - projects: {len(resume_data.get('projects', []))} items")
    
    # Show header details
    header = resume_data.get('header', {})
    print(f"\n3. Header Content:")
    print(f"   Name: {header.get('name')}")
    print(f"   Title: {header.get('title')}")
    
    # Show skills
    skills = resume_data.get('skills', [])
    print(f"\n4. Skills ({len(skills)} total):")
    for skill in skills[:5]:
        print(f"   - {skill.get('name')}: {skill.get('level')}%")
    
    # Check PDF
    pdf_path = data.get('pdf_path')
    print(f"\n5. PDF Generation:")
    print(f"   Path: {pdf_path}")
    
    if pdf_path and os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"   Size: {size} bytes")
        print(f"   ✓ PDF file exists!")
    else:
        print(f"   ✗ PDF file not found")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    
    return True

def test_resume_tailor():
    print("\n" + "=" * 60)
    print("RESUME TAILORING TEST")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/resume/tailor",
        json={
            "user_id": 1,
            "target_role": "Backend Engineer",
            "target_company": "Amazon",
            "job_description": """
            We are looking for a Backend Engineer with strong Python and 
            AWS experience. Experience with microservices architecture 
            and database optimization is required.
            """
        },
        timeout=120
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        print(f"Match Score: {data.get('match_score', 'N/A')}%")
        print(f"PDF Path: {data.get('pdf_path')}")
        print("✓ Tailoring successful!")
    else:
        print(f"Error: {data.get('error', 'Unknown error')}")
    
    return response.status_code == 200

if __name__ == "__main__":
    # Check server health first
    try:
        health = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if health.status_code != 200:
            print("Server not healthy!")
            exit(1)
    except:
        print("Server not running!")
        exit(1)
    
    # Run tests
    test_full_resume_generation()
    print()
    test_resume_tailor()
