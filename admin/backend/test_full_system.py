"""
전체 시스템 통합 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3001"

print("="*80)
print("🧪 전체 시스템 통합 테스트")
print("="*80)

# 1. 로그인 테스트
print("\n1️⃣ 로그인 API 테스트")
print("-" * 80)

login_data = {
    "username": "orion0321",
    "password": "!thdwlstn00"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": FRONTEND_URL
        },
        timeout=10
    )
    
    print(f"   ✓ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        login_result = response.json()
        print(f"   ✓ 로그인 성공!")
        print(f"   ✓ Username: {login_result.get('username')}")
        print(f"   ✓ Token Type: {login_result.get('token_type')}")
        print(f"   ✓ Access Token: {login_result.get('access_token')[:50]}...")
        
        token = login_result.get('access_token')
        
        # 2. SIM 카드 목록 조회
        print("\n2️⃣ SIM 카드 목록 조회 API 테스트")
        print("-" * 80)
        
        sim_response = requests.get(
            f"{BASE_URL}/api/v1/sims",
            headers={
                "Authorization": f"Bearer {token}",
                "Origin": FRONTEND_URL
            },
            timeout=10
        )
        
        print(f"   ✓ Status Code: {sim_response.status_code}")
        
        if sim_response.status_code == 200:
            sims = sim_response.json()
            print(f"   ✓ 등록된 SIM 카드: {len(sims)}개")
            
            for sim in sims:
                print(f"      - {sim.get('sim_number')} ({sim.get('carrier')}) - {sim.get('status')}")
        else:
            print(f"   ❌ SIM 조회 실패: {sim_response.text}")
        
        # 3. 플랫폼 계정 목록 조회
        print("\n3️⃣ 플랫폼 계정 목록 조회 API 테스트")
        print("-" * 80)
        
        accounts_response = requests.get(
            f"{BASE_URL}/api/v1/platform-accounts",
            headers={
                "Authorization": f"Bearer {token}",
                "Origin": FRONTEND_URL
            },
            timeout=10
        )
        
        print(f"   ✓ Status Code: {accounts_response.status_code}")
        
        if accounts_response.status_code == 200:
            accounts = accounts_response.json()
            print(f"   ✓ 등록된 플랫폼 계정: {len(accounts)}개")
            
            for account in accounts:
                print(f"      - {account.get('account_name')} (Platform ID: {account.get('platform_id')}) - {account.get('status')}")
        else:
            print(f"   ❌ 계정 조회 실패: {accounts_response.text}")
        
        # 4. 플랫폼 목록 조회 (인증 불필요)
        print("\n4️⃣ 플랫폼 목록 조회 API 테스트")
        print("-" * 80)
        
        platforms_response = requests.get(
            f"{BASE_URL}/api/v1/platforms",
            headers={"Origin": FRONTEND_URL},
            timeout=10
        )
        
        print(f"   ✓ Status Code: {platforms_response.status_code}")
        
        if platforms_response.status_code == 200:
            platforms = platforms_response.json()
            print(f"   ✓ 사용 가능한 플랫폼: {len(platforms)}개")
            
            for platform in platforms[:5]:  # 처음 5개만
                print(f"      - {platform.get('platform_name')} (ID: {platform.get('id')})")
        else:
            print(f"   ❌ 플랫폼 조회 실패: {platforms_response.text}")
        
        # 5. Agent 목록 조회
        print("\n5️⃣ Agent 목록 조회 API 테스트")
        print("-" * 80)
        
        agents_response = requests.get(
            f"{BASE_URL}/api/v1/agents",
            headers={
                "Authorization": f"Bearer {token}",
                "Origin": FRONTEND_URL
            },
            timeout=10
        )
        
        print(f"   ✓ Status Code: {agents_response.status_code}")
        
        if agents_response.status_code == 200:
            agents = agents_response.json()
            print(f"   ✓ 등록된 Agent: {len(agents)}개")
        else:
            print(f"   ❌ Agent 조회 실패: {agents_response.text}")
        
        # 6. Job 목록 조회
        print("\n6️⃣ Job 목록 조회 API 테스트")
        print("-" * 80)
        
        jobs_response = requests.get(
            f"{BASE_URL}/api/v1/jobs",
            headers={
                "Authorization": f"Bearer {token}",
                "Origin": FRONTEND_URL
            },
            timeout=10
        )
        
        print(f"   ✓ Status Code: {jobs_response.status_code}")
        
        if jobs_response.status_code == 200:
            jobs = jobs_response.json()
            print(f"   ✓ 등록된 Job: {len(jobs)}개")
        else:
            print(f"   ❌ Job 조회 실패: {jobs_response.text}")
        
        print("\n" + "="*80)
        print("✅ 전체 시스템 통합 테스트 완료!")
        print("="*80)
        print(f"\n📊 요약:")
        print(f"   - 로그인: ✅")
        print(f"   - SIM 카드 조회: {'✅' if sim_response.status_code == 200 else '❌'}")
        print(f"   - 플랫폼 계정 조회: {'✅' if accounts_response.status_code == 200 else '❌'}")
        print(f"   - 플랫폼 목록: {'✅' if platforms_response.status_code == 200 else '❌'}")
        print(f"   - Agent 조회: {'✅' if agents_response.status_code == 200 else '❌'}")
        print(f"   - Job 조회: {'✅' if jobs_response.status_code == 200 else '❌'}")
        print(f"\n🌐 Frontend URL: {FRONTEND_URL}")
        print(f"🔗 Backend API URL: {BASE_URL}")
        
    else:
        print(f"   ❌ 로그인 실패!")
        print(f"   ❌ Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Backend 서버에 연결할 수 없습니다!")
    print(f"   ❌ URL: {BASE_URL}")
    print("   ❌ Backend 서버가 실행 중인지 확인하세요.")
except Exception as e:
    print(f"   ❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
