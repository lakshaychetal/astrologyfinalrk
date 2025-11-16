"""
Quick API Test Script
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_signup():
    print("\n1. Testing Signup...")
    response = requests.post(f"{BASE_URL}/api/signup", json={
        "email": "test@example.com",
        "password": "test123",
        "name": "Test User"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get("token")

def test_login():
    print("\n2. Testing Login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "email": "admin@astrology.ai",
        "password": "admin123"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get("token")

def test_profile(token):
    print("\n3. Testing Get Profile...")
    response = requests.get(f"{BASE_URL}/api/me", headers={
        "Authorization": f"Bearer {token}"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_chat(token):
    print("\n4. Testing AI Chat...")
    response = requests.post(f"{BASE_URL}/api/chat", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "How will my spouse look?",
            "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n7th House: Venus in Capricorn",
            "niche": "Love & Relationships"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result['response'][:200]}...")
        print(f"Complexity: {result['complexity']}")
    else:
        print(f"Error: {response.json()}")

def test_admin_users(admin_token):
    print("\n5. Testing Admin - Get All Users...")
    response = requests.get(f"{BASE_URL}/api/admin/users", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    print(f"Status: {response.status_code}")
    print(f"Users: {len(response.json())} found")

if __name__ == "__main__":
    print("🧪 Starting API Tests...")
    
    # Test user flow
    user_token = test_signup()
    if user_token:
        test_profile(user_token)
        test_chat(user_token)
    
    # Test admin flow
    admin_token = test_login()
    if admin_token:
        test_admin_users(admin_token)
    
    print("\n✅ Tests completed!")
