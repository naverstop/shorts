"""Test auth endpoint with FastAPI TestClient"""
import sys
sys.path.insert(0, 'c:\\shorts\\admin\\backend')

from fastapi.testclient import TestClient
from app.main import app
import traceback

client = TestClient(app)

print("🔐 Testing /api/v1/auth/register endpoint...\n")

test_data = {
    "username": "directtest001",
    "email": "directtest001@test.com",
    "password": "password123"
}

print(f"Request data: {test_data}\n")

try:
    response = client.post("/api/v1/auth/register", json=test_data)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}\n")
    
    if response.status_code == 201 or response.status_code == 200:
        print("✅ SUCCESS!")
        user = response.json()
        print(f"   User ID: {user.get('id')}")
        print(f"   Username: {user.get('username')}")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
    else:
        print(f"❌ FAILED with status {response.status_code}")
        if response.text:
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Raw response: {response.text}")
                
except Exception as e:
    print(f"\n❌ Exception occurred: {type(e).__name__}: {e}")
    traceback.print_exc()
