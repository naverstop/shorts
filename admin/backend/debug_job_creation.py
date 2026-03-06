"""
간단한 Job 생성 테스트
"""
import requests

BASE_URL = "http://127.0.0.1:8001"

# 로그인
login_data = {"username": "quotauser093543", "password": "test1234"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
print(f"로그인: {response.status_code}")

if response.status_code != 200:
    print("로그인 실패")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Job 생성
job_data = {
    "title": "Test Job",
    "script": "Test script",
    "source_language": "ko",
    "target_languages": ["ko"],
    "platform_id": 1
}

print(f"\n요청 데이터: {job_data}\n")

response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, headers=headers)

print(f"응답 Status: {response.status_code}")
print(f"응답 Headers: {dict(response.headers)}\n")
print(f"응답 본문: {response.text[:500]}")

if response.status_code == 201:
    print("\n✅ Job 생성 성공!")
    print(response.json())
else:
    print("\n❌ Job 생성 실패")
