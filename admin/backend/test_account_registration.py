"""
플랫폼 계정 등록 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"
USERNAME = "orion0321"
PASSWORD = "!thdwlstn00"

def login():
    """로그인하여 액세스 토큰 획득"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return None

def get_sims(token):
    """등록된 SIM 카드 목록 가져오기"""
    response = requests.get(
        f"{BASE_URL}/api/v1/sims/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return []

def get_platforms(token):
    """플랫폼 목록 가져오기"""
    response = requests.get(
        f"{BASE_URL}/api/v1/platforms",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return []

def create_platform_account(token, account_data):
    """플랫폼 계정 등록"""
    response = requests.post(
        f"{BASE_URL}/api/v1/platform-accounts/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=account_data
    )
    return response

def main():
    print("="*80)
    print("🧪 플랫폼 계정 등록 테스트")
    print("="*80)
    
    # 로그인
    print("\n1️⃣ 로그인")
    print("-"*80)
    token = login()
    if not token:
        return
    print(f"✓ 로그인 성공!")
    
    # SIM 카드 조회
    print("\n2️⃣ SIM 카드 조회")
    print("-"*80)
    sims = get_sims(token)
    print(f"✓ 총 {len(sims)}개 SIM 카드 발견")
    for sim in sims:
        print(f"   - ID: {sim['id']}, {sim['sim_number']} ({sim['carrier']})")
    
    if len(sims) == 0:
        print("❌ 등록된 SIM이 없습니다.")
        return
    
    # 플랫폼 목록 조회
    print("\n3️⃣ 플랫폼 목록 조회")
    print("-"*80)
    platforms = get_platforms(token)
    youtube_platform = None
    for platform in platforms:
        if platform.get("platform_name") == "YouTube":
            youtube_platform = platform
            break
    
    if not youtube_platform:
        print("❌ YouTube 플랫폼을 찾을 수 없습니다.")
        return
    
    print(f"✓ YouTube 플랫폼 ID: {youtube_platform['id']}")
    
    # 각 SIM에 대해 YouTube 계정 등록
    print("\n4️⃣ YouTube 계정 등록")
    print("-"*80)
    
    test_accounts = [
        {"sim_id": 0, "account_name": "테스트채널_1", "identifier": "test_channel_001"},
        {"sim_id": 1, "account_name": "테스트채널_2", "identifier": "test_channel_002"},
        {"sim_id": 2, "account_name": "테스트채널_3", "identifier": "test_channel_003"},
    ]
    
    registered_count = 0
    for i, sim in enumerate(sims):
        if i >= len(test_accounts):
            break
            
        account_info = test_accounts[i]
        account_data = {
            "sim_id": sim["id"],
            "platform_id": youtube_platform["id"],
            "account_name": account_info["account_name"],
            "account_identifier": account_info["identifier"],
            "credentials": {
                "api_key": f"test_api_key_{i+1}",
                "refresh_token": f"test_refresh_token_{i+1}"
            },
            "is_primary": (i == 0),
            "notes": f"테스트 계정 {i+1}"
        }
        
        response = create_platform_account(token, account_data)
        
        if response.status_code in [200, 201]:
            print(f"   ✓ 계정 등록 성공: {account_info['account_name']} (SIM: {sim['sim_number']})")
            registered_count += 1
        else:
            try:
                error_detail = response.json()
                print(f"   ❌ 계정 등록 실패: {account_info['account_name']} - {error_detail}")
            except:
                print(f"   ❌ 계정 등록 실패: {account_info['account_name']} - Status {response.status_code}")
    
    print(f"\n   ✓ 총 {registered_count}개 계정 등록 완료")
    
    # 최종 데이터 확인
    print("\n5️⃣ 최종 데이터 확인")
    print("-"*80)
    
    # 플랫폼 계정 조회
    response = requests.get(
        f"{BASE_URL}/api/v1/platform-accounts/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        accounts = response.json()
        print(f"\n   🔐 등록된 플랫폼 계정: {len(accounts)}개")
        for account in accounts:
            print(f"      - {account['account_name']} ({account.get('account_identifier', 'N/A')})")
    
    print("\n" + "="*80)
    print("✅ 플랫폼 계정 등록 테스트 완료!")
    print("="*80)
    print("\n🌐 Frontend에서 확인: http://localhost:3001")
    print("   1. 로그인: orion0321 / !thdwlstn00")
    print("   2. 'SIM 카드' 메뉴 클릭")
    print("   3. '계정 관리' 메뉴 클릭")

if __name__ == "__main__":
    main()
