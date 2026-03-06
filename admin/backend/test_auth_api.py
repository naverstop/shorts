"""Test auth API with detailed error messages"""
import requests
import json
from datetime import datetime

# Generate unique username
timestamp = datetime.now().strftime("%H%M%S")
username = f"test{timestamp}"

print(f"🔐 Testing auth API with username: {username}\n")

# Test data
data = {
    "username": username,
    "email": f"{username}@test.com",
    "password": "password123"
}

print("📤 Request:")
print(f"   URL: http://localhost:8001/api/v1/auth/register")
print(f"   Body: {json.dumps(data, indent=6)}\n")

try:
    response = requests.post(
        "http://localhost:8001/api/v1/auth/register",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print("📥 Response:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    print(f"\n   Response Body:")
    print(f"   {response.text}\n")
    
    if response.status_code == 200 or response.status_code == 201:
        user = response.json()
        print(f"✅ Success!")
        print(f"   User ID: {user.get('id')}")
        print(f"   Username: {user.get('username')}")
        print(f"   Role: {user.get('role')}")
    else:
        print(f"❌ Failed with status code {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
