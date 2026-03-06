"""
SIM 등록 디버그 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3001"

# 1. 로그인
login_data = {"username": "orion0321", "password": "!thdwlstn00"}
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=10
)

if response.status_code != 200:
    print(f"❌ 로그인 실패: {response.text}")
    exit(1)

token = response.json().get('access_token')
print(f"✓ 로그인 성공!")

# 2. SIM 등록 테스트 (상세 에러 출력)
print("\n📱 SIM 카드 등록 테스트...")

sim_data = {
    "sim_number": "010-9999-9999",
    "carrier": "SKT",
    "google_email": "debug_test@gmail.com",
    "nickname": "디버그 테스트 SIM"
}

print(f"   - Request Data: {json.dumps(sim_data, indent=2, ensure_ascii=False)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/sims",
        json=sim_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Origin": FRONTEND_URL
        },
        timeout=10
    )
    
    print(f"   - Response Status: {response.status_code}")
    print(f"   - Response Headers: {dict(response.headers)}")
    print(f"   - Response Body: {response.text}")
    
    if response.status_code == 201:
        sim = response.json()
        print(f"\n✓ SIM 등록 성공!")
        print(f"   - ID: {sim.get('id')}")
        print(f"   - SIM Number: {sim.get('sim_number')}")
        print(f"   - Status: {sim.get('status')}")
    else:
        print(f"\n❌ SIM 등록 실패!")
        try:
            error_detail = response.json()
            print(f"   - Error Detail: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
        except:
            print(f"   - Raw Error: {response.text}")
            
except Exception as e:
    print(f"\n❌ 예외 발생: {e}")
    import traceback
    traceback.print_exc()
