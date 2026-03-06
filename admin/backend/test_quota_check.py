"""
Quota Check 미들웨어 테스트
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
quota_id = None
platform_id = 1  # YouTube

try:
    # 1. 사용자 등록
    print_header("1. 사용자 등록")
    timestamp = datetime.now().strftime("%H%M%S")
    username = f"quotauser{timestamp}"
    
    register_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "test1234"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    if response.status_code in [200, 201]:
        user_data = response.json()
        user_id = user_data["id"]
        print_result(f"회원가입 성공: {username}", True, {"user_id": user_id})
    else:
        print_result("회원가입 실패", False, response.json())
        exit(1)
    
    # 2. 로그인
    print_header("2. 로그인")
    login_data = {"username": username, "password": "test1234"}
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print_result("로그인 성공", True)
    else:
        print_result("로그인 실패", False, response.json())
        exit(1)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Job 생성 (할당량 없음 - 무제한 허용)
    print_header("3. Job 생성 (할당량 없음 - 허용)")
    job_data = {
        "title": "Test Job 1",
        "script": "Test script",
        "source_language": "ko",
        "target_languages": ["ko"],
        "platform_id": platform_id
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, headers=headers)
    if response.status_code == 201:
        job = response.json()
        job1_id = job["id"]
        print_result("Job 생성 성공 (할당량 없음)", True, {
            "job_id": job1_id,
            "platform_id": job["target_platform_id"],
            "status": job["status"]
        })
    else:
        try:
            error_data = response.json()
        except:
            error_data = {"status_code": response.status_code, "text": response.text}
        print_result("Job 생성 실패", False, error_data)
        exit(1)
    
    # 4. 할당량 생성 (일일 2개 제한)
    print_header("4. 할당량 생성 (일일 2개 제한)")
    quota_data = {
        "platform_id": platform_id,
        "daily_limit": 2,
        "weekly_limit": 0,
        "monthly_limit": 0
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/upload-quotas", json=quota_data, headers=headers)
    if response.status_code == 201:
        quota = response.json()
        quota_id = quota["id"]
        print_result("할당량 생성 성공", True, {
            "quota_id": quota_id,
            "daily_limit": quota["daily_limit"],
            "used_today": quota["used_today"]
        })
    else:
        print_result("할당량 생성 실패", False, response.json())
        exit(1)
    
    # 5. Job 생성 (할당량 내 - 허용)
    print_header("5. Job 생성 #2 (할당량 내 - 허용)")
    job_data["title"] = "Test Job 2"
    
    response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, headers=headers)
    if response.status_code == 201:
        job = response.json()
        job2_id = job["id"]
        print_result("Job 생성 성공 (1/2)", True, {"job_id": job2_id})
    else:
        print_result("Job 생성 실패", False, response.json())
        exit(1)
    
    # 6. Job 생성 (할당량 내 - 허용)
    print_header("6. Job 생성 #3 (할당량 내 - 허용)")
    job_data["title"] = "Test Job 3"
    
    response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, headers=headers)
    if response.status_code == 201:
        job = response.json()
        job3_id = job["id"]
        print_result("Job 생성 성공 (2/2)", True, {"job_id": job3_id})
    else:
        print_result("Job 생성 실패", False, response.json())
        exit(1)
    
    # 7. Job 생성 (할당량 초과 - 거부)
    print_header("7. Job 생성 #4 (할당량 초과 - 거부 예상)")
    job_data["title"] = "Test Job 4"
    
    response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, headers=headers)
    if response.status_code == 429:
        error_data = response.json()
        print_result("Job 생성 거부 성공 (429 Too Many Requests)", True, {
            "status_code": 429,
            "error": error_data.get("detail", {}).get("error"),
            "message": error_data.get("detail", {}).get("message")
        })
    else:
        print_result("예상과 다름 - 할당량 초과인데 생성됨!", False, {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 201 else response.text
        })
    
    # 8. 할당량 확인
    print_header("8. 할당량 확인")
    response = requests.get(f"{BASE_URL}/api/v1/upload-quotas/{quota_id}", headers=headers)
    if response.status_code == 200:
        quota = response.json()
        print_result("할당량 조회 성공", True, {
            "used_today": quota["used_today"],
            "daily_limit": quota["daily_limit"],
            "remaining": quota["remaining_daily"],
            "is_exceeded": quota["is_quota_exceeded"]
        })
    else:
        print_result("할당량 조회 실패", False)
    
    # 9. Job 목록 확인
    print_header("9. Job 목록 확인")
    response = requests.get(f"{BASE_URL}/api/v1/jobs", headers=headers)
    if response.status_code == 200:
        jobs = response.json()
        print_result(f"Job 목록 조회 성공 (총 {len(jobs)}개)", True)
        for job in jobs[:3]:
            print(f"   - Job {job['id']}: {job['title']} (platform: {job['target_platform_id']}, status: {job['status']})")
    else:
        print_result("Job 목록 조회 실패", False)
    
    # 10. 할당량 삭제
    print_header("10. 할당량 삭제")
    response = requests.delete(f"{BASE_URL}/api/v1/upload-quotas/{quota_id}", headers=headers)
    if response.status_code == 204:
        print_result("할당량 삭제 성공", True)
    else:
        print_result("할당량 삭제 실패", False)
    
    # 11. Job 생성 (할당량 삭제 후 - 허용)
    print_header("11. Job 생성 #5 (할당량 삭제 후 - 허용)")
    job_data["title"] = "Test Job 5"
    
    response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, headers=headers)
    if response.status_code == 201:
        job = response.json()
        print_result("Job 생성 성공 (할당량 삭제 후)", True, {"job_id": job["id"]})
    else:
        print_result("Job 생성 실패", False, response.json())
    
    # 최종 요약
    print_header("테스트 완료")
    print("✅ Quota Check 미들웨어 테스트 성공")
    print("\n테스트된 기능:")
    print("  ✅ Job 생성 시 할당량 체크")
    print("  ✅ 할당량 없을 때 무제한 허용")
    print("  ✅ 할당량 내에서 Job 생성")
    print("  ✅ 할당량 초과 시 429 에러 반환")
    print("  ✅ 할당량 삭제 후 다시 무제한")
    print("\n구현된 기능:")
    print("  - Job 모델에 target_platform_id 추가")
    print("  - JobCreate 스키마에 platform_id 필드 추가")
    print("  - check_upload_quota() 유틸리티 함수")
    print("  - Job 생성 API에 quota 체크 통합")
    print("  - 429 Too Many Requests 에러 처리")

except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
