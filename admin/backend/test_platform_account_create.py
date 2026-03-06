"""
플랫폼 계정 생성 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"
USERNAME = "orion0321"
PASSWORD = "!thdwlstn00"

def test_platform_account_creation():
    print("="*80)
    print("🧪 플랫폼 계정 생성 테스트")
    print("="*80)
    
    # 1. 로그인
    print("\n1️⃣ 로그인")
    print("-"*80)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code != 200:
        print(f"❌ 로그인 실패: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    token = response.json()["access_token"]
    print(f"✓ 로그인 성공!")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. SIM 카드 조회
    print("\n2️⃣ SIM 카드 조회")
    print("-"*80)
    response = requests.get(f"{BASE_URL}/api/v1/sims", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ SIM 조회 실패: Status {response.status_code}")
        return
    
    sims = response.json()
    if len(sims) == 0:
        print("❌ 등록된 SIM이 없습니다. 먼저 SIM을 등록하세요.")
        return
    
    sim_id = sims[0]["id"]
    print(f"✓ SIM 조회 성공! 사용할 SIM ID: {sim_id} ({sims[0]['sim_number']})")
    
    # 3. 플랫폼 계정 생성
    print("\n3️⃣ 플랫폼 계정 생성")
    print("-"*80)
    account_data = {
        "sim_id": sim_id,
        "platform_id": 1,  # YouTube
        "account_name": "orion0321@gmail.com",
        "account_identifier": "@orion_shorts",
        "is_primary": True,
        "credentials": {}
    }
    
    print(f"요청 데이터: {json.dumps(account_data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/platform-accounts",
        headers={**headers, "Content-Type": "application/json"},
        json=account_data
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 201:
        account = response.json()
        print(f"\n✓ 플랫폼 계정 생성 성공!")
        print(f"   - ID: {account['id']}")
        print(f"   - 계정명: {account['account_name']}")
        print(f"   - SIM ID: {account['sim_id']}")
        print(f"   - 플랫폼: {account['platform_id']}")
    else:
        print(f"\n❌ 플랫폼 계정 생성 실패: Status {response.status_code}")
        print(f"   Response: {response.text}")
    
    # 4. 생성 확인
    print("\n4️⃣ 플랫폼 계정 목록 조회")
    print("-"*80)
    response = requests.get(f"{BASE_URL}/api/v1/platform-accounts", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 목록 조회 실패: Status {response.status_code}")
        return
    
    accounts = response.json()
    print(f"✓ 목록 조회 성공! 총 {len(accounts)}개")
    for acc in accounts:
        print(f"   - ID: {acc['id']}, {acc['account_name']} (SIM: {acc['sim_id']})")

if __name__ == "__main__":
    test_platform_account_creation()
