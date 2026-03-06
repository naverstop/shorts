"""
가상 데이터 등록 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3001"

print("="*80)
print("🧪 가상 데이터 등록 테스트")
print("="*80)

# 1. 로그인
print("\n1️⃣ 로그인")
print("-" * 80)

login_data = {
    "username": "orion0321",
    "password": "!thdwlstn00"
}

response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": FRONTEND_URL},
    timeout=10
)

if response.status_code != 200:
    print(f"❌ 로그인 실패: {response.text}")
    exit(1)

token = response.json().get('access_token')
print(f"✓ 로그인 성공! Token: {token[:50]}...")

# 2. SIM 카드 등록
print("\n2️⃣ SIM 카드 등록")
print("-" * 80)

sim_data_list = [
    {
        "sim_number": "010-1111-1111",
        "carrier": "SKT",
        "google_email": "test1@gmail.com",
        "nickname": "테스트 SIM 1"
    },
    {
        "sim_number": "010-2222-2222",
        "carrier": "KT",
        "google_email": "test2@gmail.com",
        "nickname": "테스트 SIM 2"
    },
    {
        "sim_number": "010-3333-3333",
        "carrier": "LG U+",
        "google_email": "test3@gmail.com",
        "nickname": "테스트 SIM 3"
    }
]

created_sims = []

for sim_data in sim_data_list:
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
        
        if response.status_code == 201:
            sim = response.json()
            created_sims.append(sim)
            print(f"   ✓ SIM 등록 성공: {sim.get('sim_number')} (ID: {sim.get('id')})")
        else:
            print(f"   ❌ SIM 등록 실패: {sim_data.get('sim_number')} - {response.text}")
    except Exception as e:
        print(f"   ❌ 오류: {sim_data.get('sim_number')} - {e}")

print(f"\n   ✓ 총 {len(created_sims)}개 SIM 카드 등록 완료")

# 3. 플랫폼 계정 등록
print("\n3️⃣ 플랫폼 계정 등록")
print("-" * 80)

if len(created_sims) == 0:
    print("   ❌ 등록된 SIM이 없어 계정 등록 불가")
else:
    # 첫 번째 SIM으로 YouTube 계정 등록
    first_sim = created_sims[0]
    
    account_data = {
        "sim_id": first_sim.get('id'),
        "platform_id": 1,  # YouTube
        "account_name": f"YouTube 테스트 계정 - {first_sim.get('sim_number')}",
        "account_identifier": f"youtube_test_{first_sim.get('id')}",
        "credentials": {
            "access_token": "test_access_token_12345",
            "refresh_token": "test_refresh_token_67890"
        },
        "is_primary": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/platform-accounts",
            json=account_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Origin": FRONTEND_URL
            },
            timeout=10
        )
        
        if response.status_code == 201:
            account = response.json()
            print(f"   ✓ 계정 등록 성공: {account.get('account_name')} (ID: {account.get('id')})")
            print(f"      - SIM: {first_sim.get('sim_number')}")
            print(f"      - Platform: YouTube")
            print(f"      - Status: {account.get('status')}")
        else:
            print(f"   ❌ 계정 등록 실패: {response.status_code}")
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

# 4. 최종 확인
print("\n4️⃣ 최종 데이터 확인")
print("-" * 80)

# SIM 목록
sim_response = requests.get(
    f"{BASE_URL}/api/v1/sims",
    headers={"Authorization": f"Bearer {token}", "Origin": FRONTEND_URL},
    timeout=10
)

if sim_response.status_code == 200:
    sims = sim_response.json()
    print(f"\n   📱 등록된 SIM 카드: {len(sims)}개")
    for sim in sims:
        print(f"      - {sim.get('sim_number')} ({sim.get('carrier')}) - {sim.get('nickname')}")

# 플랫폼 계정 목록
accounts_response = requests.get(
    f"{BASE_URL}/api/v1/platform-accounts",
    headers={"Authorization": f"Bearer {token}", "Origin": FRONTEND_URL},
    timeout=10
)

if accounts_response.status_code == 200:
    accounts = accounts_response.json()
    print(f"\n   🔐 등록된 플랫폼 계정: {len(accounts)}개")
    for account in accounts:
        print(f"      - {account.get('account_name')} (Status: {account.get('status')})")

print("\n" + "="*80)
print("✅ 가상 데이터 등록 테스트 완료!")
print("="*80)
print(f"\n🌐 Frontend에서 확인: http://localhost:3001")
print(f"   1. 로그인: orion0321 / !thdwlstn00")
print(f"   2. 'SIM 카드' 메뉴 클릭")
print(f"   3. '계정 관리' 메뉴 클릭")
