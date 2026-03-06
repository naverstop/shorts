"""
간단한 디버깅 스크립트 - 에러 메시지 상세 확인
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

# 1. 로그인
login_data = {"username": "quotatest091717", "password": "test1234"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
print(f"로그인 Status: {response.status_code}")

if response.status_code!= 200:
    print("로그인 실패")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Token: {token[:30]}...\n")

# 2. 할당량 생성 시도
quota_data = {
    "platform_id": 1,
    "daily_limit": 10,
    "weekly_limit": 50,
    "monthly_limit": 200
}

print(f"요청 데이터: {json.dumps(quota_data, indent=2)}\n")

response = requests.post(
    f"{BASE_URL}/api/v1/upload-quotas",
    json=quota_data,
    headers=headers
)

print(f"응답 Status Code: {response.status_code}")
print(f"응답 Headers: {dict(response.headers)}\n")

# 응답 본문 출력 (HTML/JSON 관계없이)
print(f"응답 본문 (처음 500자):")
print(response.text[:500])
print("\n...")

# JSON 파싱 시도
try:
    json_response = response.json()
    print(f"\nJSON 응답:")
    print(json.dumps(json_response, indent=2, ensure_ascii=False))
except:
    print("\nJSON 파싱 실패 - HTML 응답일 가능성 있음")
