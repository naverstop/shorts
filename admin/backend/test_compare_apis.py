"""
다른 API 엔드포인트 테스트
"""
import requests

BASE_URL = "http://127.0.0.1:8001"

# 로그인
login_data = {"username": "quotatest092547", "password": "test1234"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Agents 목록 조회 (비교용)
print("=== Agents API ===")
response = requests.get(f"{BASE_URL}/api/v1/agents", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"✅ Agents API 작동 (agents: {len(response.json())}개)")
else:
    print(f"❌ Agents API 오류: {response.text}")

# Jobs 목록 조회 (비교용)
print("\n=== Jobs API ===")
response = requests.get(f"{BASE_URL}/api/v1/jobs", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"✅ Jobs API 작동 (jobs: {len(response.json())}개)")
else:
    print(f"❌ Jobs API 오류: {response.text}")

# Upload Quotas 목록 조회
print("\n=== Upload Quotas API ===")
response = requests.get(f"{BASE_URL}/api/v1/upload-quotas", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"✅ Upload Quotas API 작동 (quotas: {len(response.json())}개)")
else:
    print(f"❌ Upload Quotas API 오류: {response.text}")
