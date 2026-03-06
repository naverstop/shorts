"""
간단한 GET 테스트
"""
import requests

BASE_URL = "http://127.0.0.1:8001"

# 로그인
login_data = {"username": "quotatest092547", "password": "test1234"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
print(f"로그인: {response.status_code}")

if response.status_code != 200:
    print("로그인 실패")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# GET /api/v1/upload-quotas (목록 조회 - 빈 목록 반환 예상)
response = requests.get(f"{BASE_URL}/api/v1/upload-quotas", headers=headers)
print(f"\n목록 조회: {response.status_code}")
if response.status_code == 200:
    print(f"결과: {response.json()}")
else:
    print(f"에러: {response.text}")
