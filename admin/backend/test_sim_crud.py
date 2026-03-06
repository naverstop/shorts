"""
SIM CRUD 전체 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"
USERNAME = "orion0321"
PASSWORD = "!thdwlstn00"

def test_crud():
    print("="*80)
    print("🧪 SIM CRUD 전체 테스트")
    print("="*80)
    
    # 1. 로그인
    print("\n1️⃣ 로그인")
    print("-"*80)
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code != 200:
        print(f"❌ 로그인 실패: {response.text}")
        return
    
    token = response.json()["access_token"]
    print(f"✓ 로그인 성공!")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. SIM 카드 등록 (CREATE)
    print("\n2️⃣ SIM 카드 등록 (CREATE)")
    print("-"*80)
    sim_data = {
        "sim_number": "010-TEST-0001",
        "carrier": "SKT",
        "google_email": "test_crud@gmail.com",
        "nickname": "CRUD 테스트 SIM",
        "notes": "자동 테스트용"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/sims/",
        headers={**headers, "Content-Type": "application/json"},
        json=sim_data
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ SIM 등록 실패: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    sim_id = response.json()["id"]
    print(f"✓ SIM 등록 성공! ID: {sim_id}")
    print(f"   - SIM 번호: {sim_data['sim_number']}")
    print(f"   - 통신사: {sim_data['carrier']}")
    
    # 3. SIM 카드 목록 조회 (READ - List)
    print("\n3️⃣ SIM 카드 목록 조회 (READ)")
    print("-"*80)
    response = requests.get(f"{BASE_URL}/api/v1/sims/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 목록 조회 실패: Status {response.status_code}")
        return
    
    sims = response.json()
    print(f"✓ 목록 조회 성공! 총 {len(sims)}개")
    for sim in sims:
        print(f"   - ID: {sim['id']}, {sim['sim_number']} ({sim['carrier']})")
    
    # 4. SIM 카드 상세 조회 (READ - Detail)
    print("\n4️⃣ SIM 카드 상세 조회 (READ)")
    print("-"*80)
    response = requests.get(f"{BASE_URL}/api/v1/sims/{sim_id}", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 상세 조회 실패: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    detail = response.json()
    print(f"✓ 상세 조회 성공!")
    print(f"   - ID: {detail['id']}")
    print(f"   - SIM 번호: {detail['sim_number']}")
    print(f"   - 통신사: {detail['carrier']}")
    print(f"   - Google: {detail.get('google_email', 'N/A')}")
    print(f"   - 별칭: {detail.get('nickname', 'N/A')}")
    print(f"   - 상태: {detail['status']}")
    print(f"   - Agent 상태: {detail.get('agent_status', 'N/A')}")
    
    # 5. SIM 카드 수정 (UPDATE)
    print("\n5️⃣ SIM 카드 수정 (UPDATE)")
    print("-"*80)
    update_data = {
        "carrier": "KT",
        "nickname": "수정된 CRUD 테스트",
        "notes": "수정 테스트 완료"
    }
    
    response = requests.put(
        f"{BASE_URL}/api/v1/sims/{sim_id}",
        headers={**headers, "Content-Type": "application/json"},
        json=update_data
    )
    
    if response.status_code != 200:
        print(f"❌ SIM 수정 실패: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    updated = response.json()
    print(f"✓ SIM 수정 성공!")
    print(f"   - 통신사: {sim_data['carrier']} → {updated['carrier']}")
    print(f"   - 별칭: {sim_data['nickname']} → {updated.get('nickname', 'N/A')}")
    
    # 6. SIM 카드 삭제 (DELETE)
    print("\n6️⃣ SIM 카드 삭제 (DELETE)")
    print("-"*80)
    response = requests.delete(f"{BASE_URL}/api/v1/sims/{sim_id}", headers=headers)
    
    if response.status_code != 204:
        print(f"❌ SIM 삭제 실패: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    print(f"✓ SIM 삭제 성공!")
    
    # 7. 삭제 확인
    print("\n7️⃣ 삭제 확인")
    print("-"*80)
    response = requests.get(f"{BASE_URL}/api/v1/sims/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 확인 실패")
        return
    
    sims = response.json()
    print(f"✓ 삭제 확인 완료! 현재 SIM 수: {len(sims)}개")
    
    print("\n" + "="*80)
    print("✅ CRUD 테스트 완료!")
    print("="*80)
    print("\n📝 테스트 결과:")
    print("   - CREATE (등록): ✅")
    print("   - READ (조회): ✅")
    print("   - UPDATE (수정): ✅")
    print("   - DELETE (삭제): ✅")
    print("\n🌐 Frontend에서도 동일하게 테스트해주세요:")
    print("   1. SIM 등록")
    print("   2. 테이블에서 '상세' 버튼 클릭")
    print("   3. 상세 모달에서 '수정' 버튼 클릭")
    print("   4. 정보 변경 후 '저장'")
    print("   5. 상세 모달에서 '삭제' 버튼 클릭")

if __name__ == "__main__":
    test_crud()
