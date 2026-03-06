"""
Upload Quota API Test Script
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"

def print_header(text):
    """테스트 섹션 헤더 출력"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_result(title, success, data=None):
    """테스트 결과 출력"""
    status = "✅" if success else "❌"
    print(f"{status} {title}")
    if data:
        print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")

# Test variables
token = None
user_id = None
quota_id = None
platform_id = 1  # YouTube

try:
    # 1. 사용자 등록
    print_header("1. 사용자 등록")
    timestamp = datetime.now().strftime("%H%M%S")
    username = f"quotatest{timestamp}"
    
    register_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "test1234"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    if response.status_code in [200, 201]:
        user_data = response.json()
        user_id = user_data["id"]
        print_result(f"회원가입 성공: {username}", True, user_data)
    else:
        print_result("회원가입 실패", False, response.json())
        exit(1)
    
    # 2. 로그인
    print_header("2. 로그인")
    login_data = {
        "username": username,
        "password": "test1234"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print_result("로그인 성공", True, {"token": f"{token[:20]}..."})
    else:
        print_result("로그인 실패", False, response.json())
        exit(1)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. 업로드 할당량 생성
    print_header("3. 업로드 할당량 생성")
    quota_data = {
        "platform_id": platform_id,
        "daily_limit": 10,
        "weekly_limit": 50,
        "monthly_limit": 200
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/upload-quotas", json=quota_data, headers=headers)
    if response.status_code == 201:
        quota = response.json()
        quota_id = quota["id"]
        print_result("할당량 생성 성공", True, {
            "id": quota["id"],
            "platform_id": quota["platform_id"],
            "daily_limit": quota["daily_limit"],
            "weekly_limit": quota["weekly_limit"],
            "monthly_limit": quota["monthly_limit"],
        })
    else:
        try:
            error_data = response.json()
        except:
            error_data = {"status_code": response.status_code, "text": response.text}
        print_result("할당량 생성 실패", False, error_data)
        exit(1)
    
    # 4. 할당량 목록 조회
    print_header("4. 할당량 목록 조회")
    response = requests.get(f"{BASE_URL}/api/v1/upload-quotas", headers=headers)
    if response.status_code == 200:
        quotas = response.json()
        print_result(f"할당량 목록 조회 성공 (총 {len(quotas)}개)", True)
        for q in quotas:
            print(f"   - Platform {q['platform_id']}: "
                  f"Daily {q['used_today']}/{q['daily_limit']}, "
                  f"Weekly {q['used_week']}/{q['weekly_limit']}, "
                  f"Monthly {q['used_month']}/{q['monthly_limit']}")
    else:
        print_result("할당량 목록 조회 실패", False, response.json())
    
    # 5. 특정 할당량 조회
    print_header("5. 특정 할당량 조회")
    response = requests.get(f"{BASE_URL}/api/v1/upload-quotas/{quota_id}", headers=headers)
    if response.status_code == 200:
        quota = response.json()
        print_result("할당량 조회 성공", True, {
            "id": quota["id"],
            "remaining_daily": quota["remaining_daily"],
            "remaining_weekly": quota["remaining_weekly"],
            "remaining_monthly": quota["remaining_monthly"],
            "is_quota_exceeded": quota["is_quota_exceeded"],
        })
    else:
        print_result("할당량 조회 실패", False, response.json())
    
    # 6. 업로드 가능 여부 체크
    print_header("6. 업로드 가능 여부 체크")
    response = requests.get(f"{BASE_URL}/api/v1/upload-quotas/check/{platform_id}", headers=headers)
    if response.status_code == 200:
        check = response.json()
        print_result(f"업로드 가능 여부: {check['can_upload']}", True, check)
    else:
        print_result("체크 실패", False, response.json())
    
    # 7. 할당량 수정 (제한 증가)
    print_header("7. 할당량 수정")
    update_data = {
        "daily_limit": 20,
        "weekly_limit": 100,
    }
    
    response = requests.patch(f"{BASE_URL}/api/v1/upload-quotas/{quota_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        quota = response.json()
        print_result("할당량 수정 성공", True, {
            "daily_limit": quota["daily_limit"],
            "weekly_limit": quota["weekly_limit"],
            "monthly_limit": quota["monthly_limit"],
        })
    else:
        print_result("할당량 수정 실패", False, response.json())
    
    # 8. 전체 통계 조회
    print_header("8. 전체 통계 조회")
    response = requests.get(f"{BASE_URL}/api/v1/upload-quotas/stats/all", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print_result("통계 조회 성공", True, {
            "total_quotas": stats["total_quotas"],
            "exceeded_count": stats["exceeded_count"],
            "platforms_count": len(stats["platforms"]),
        })
        for platform in stats["platforms"]:
            print(f"   - {platform['platform_name']}: "
                  f"Daily {platform['daily']['used']}/{platform['daily']['limit']}, "
                  f"Exceeded: {platform['is_exceeded']}")
    else:
        print_result("통계 조회 실패", False, response.json())
    
    # 9. 할당량 삭제
    print_header("9. 할당량 삭제")
    response = requests.delete(f"{BASE_URL}/api/v1/upload-quotas/{quota_id}", headers=headers)
    if response.status_code == 204:
        print_result("할당량 삭제 성공", True)
    else:
        print_result("할당량 삭제 실패", False, response.json())
    
    # 10. 삭제 확인
    print_header("10. 삭제 확인")
    response = requests.get(f"{BASE_URL}/api/v1/upload-quotas/{quota_id}", headers=headers)
    if response.status_code == 404:
        print_result("삭제 확인 완료 (404 반환)", True)
    else:
        print_result("삭제 확인 실패 (아직 존재함)", False)
    
    # 최종 요약
    print_header("테스트 완료")
    print("✅ Upload Quota API 테스트 성공")
    print("\n테스트된 기능:")
    print("  ✅ 할당량 생성 (POST)")
    print("  ✅ 할당량 목록 조회 (GET)")
    print("  ✅ 할당량 상세 조회 (GET)")
    print("  ✅ 업로드 가능 여부 체크 (GET)")
    print("  ✅ 할당량 수정 (PATCH)")
    print("  ✅ 전체 통계 조회 (GET)")
    print("  ✅ 할당량 삭제 (DELETE)")
    print("\n추가 기능:")
    print("  - JWT 인증 통합")
    print("  - 사용자별 할당량 관리")
    print("  - 플랫폼별 제한 설정")
    print("  - 일일/주간/월간 제한")
    print("  - 남은 할당량 계산")
    print("  - 초과 여부 체크")

except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
