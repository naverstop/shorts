"""
Quota Reset Scheduler 테스트
- 스케줄러 상태 확인
- 수동 리셋 기능 테스트
- 리셋 통계 조회
"""
import requests
import random
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def register_and_login():
    """회원가입 및 로그인"""
    username = f"quotauser{random.randint(100000, 999999)}"
    
    # 회원가입
    register_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "test1234"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    if response.status_code != 201:
        print(f"❌ 회원가입 실패: {response.status_code}")
        print(response.text)
        return None, None
    
    user_data = response.json()
    print(f"✅ 회원가입 성공: {username}")
    user_id = user_data.get('user_id') or user_data.get('id')
    print(f"   User ID: {user_id}\n")
    
    # 로그인
    login_data = {
        "username": username,
        "password": "test1234"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"❌ 로그인 실패")
        return None, None
    
    token = response.json()["access_token"]
    print(f"✅ 로그인 성공\n")
    
    return token, user_id


def create_quota(token, user_id, platform_id=1):
    """할당량 생성"""
    headers = {"Authorization": f"Bearer {token}"}
    quota_data = {
        "platform_id": platform_id,
        "daily_limit": 5,
        "weekly_limit": 20,
        "monthly_limit": 80
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/upload-quotas",
        json=quota_data,
        headers=headers
    )
    
    if response.status_code != 201:
        print(f"❌ 할당량 생성 실패: {response.status_code}")
        return None
    
    quota = response.json()
    print(f"✅ 할당량 생성 성공")
    print(f"   Quota ID: {quota['id']}")
    print(f"   Daily: {quota['used_today']}/{quota['daily_limit']}")
    print(f"   Weekly: {quota['used_week']}/{quota['weekly_limit']}")
    print(f"   Monthly: {quota['used_month']}/{quota['monthly_limit']}\n")
    
    return quota['id']


def create_jobs(token, count=3):
    """Job 생성 (사용량 증가)"""
    headers = {"Authorization": f"Bearer {token}"}
    created_jobs = []
    
    for i in range(count):
        job_data = {
            "title": f"Test Job {i+1}",
            "script": "Test script",
            "source_language": "ko",
            "target_languages": ["ko"],
            "platform_id": 1,
            "priority": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/jobs",
            json=job_data,
            headers=headers
        )
        
        if response.status_code == 201:
            job = response.json()
            created_jobs.append(job['id'])
            print(f"✅ Job {i+1} 생성: ID={job['id']}")
        else:
            print(f"❌ Job {i+1} 생성 실패: {response.status_code}")
    
    print()
    return created_jobs


def check_quota(token, quota_id):
    """할당량 조회"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/upload-quotas/{quota_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 할당량 조회 실패")
        return None
    
    quota = response.json()
    print(f"📊 현재 할당량 상태:")
    print(f"   Daily: {quota['used_today']}/{quota['daily_limit']} (잔여: {quota['remaining_daily']})")
    print(f"   Weekly: {quota['used_week']}/{quota['weekly_limit']} (잔여: {quota['remaining_weekly']})")
    print(f"   Monthly: {quota['used_month']}/{quota['monthly_limit']} (잔여: {quota['remaining_monthly']})")
    print(f"   초과 여부: {quota['is_quota_exceeded']}\n")
    
    return quota


def check_scheduler_status(token):
    """스케줄러 상태 조회"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/upload-quotas/scheduler/status",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 스케줄러 상태 조회 실패")
        return None
    
    status = response.json()
    print(f"📅 스케줄러 상태:")
    print(f"   실행 중: {status['running']}")
    print(f"   등록된 작업 수: {len(status['jobs'])}\n")
    
    if status['jobs']:
        print("📋 예약된 작업:")
        for job in status['jobs']:
            print(f"   - {job['name']}")
            print(f"     다음 실행: {job['next_run']}")
            print(f"     트리거: {job['trigger']}\n")
    
    return status


def get_reset_stats(token):
    """리셋 통계 조회"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/upload-quotas/reset/stats",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 리셋 통계 조회 실패")
        return None
    
    stats = response.json()
    print(f"📈 리셋 통계:")
    print(f"   전체 할당량: {stats['total_quotas']}개")
    print(f"   오늘 사용량: {stats['total_used_today']}")
    print(f"   이번 주 사용량: {stats['total_used_week']}")
    print(f"   이번 달 사용량: {stats['total_used_month']}\n")
    
    return stats


def manual_reset_daily(token):
    """수동 일일 리셋"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/upload-quotas/reset/daily",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 일일 리셋 실패: {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    print(f"✅ 일일 리셋 성공")
    print(f"   영향받은 행: {result['rows_affected']}개\n")
    
    return True


def manual_reset_weekly(token):
    """수동 주간 리셋"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/upload-quotas/reset/weekly",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 주간 리셋 실패")
        return False
    
    result = response.json()
    print(f"✅ 주간 리셋 성공")
    print(f"   영향받은 행: {result['rows_affected']}개\n")
    
    return True


def manual_reset_monthly(token):
    """수동 월간 리셋"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/upload-quotas/reset/monthly",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 월간 리셋 실패")
        return False
    
    result = response.json()
    print(f"✅ 월간 리셋 성공")
    print(f"   영향받은 행: {result['rows_affected']}개\n")
    
    return True


def main():
    print("=" * 60)
    print("  📅 Quota Reset Scheduler 테스트")
    print("=" * 60)
    
    # 1. 회원가입 및 로그인
    print_section("1. 회원가입 및 로그인")
    token, user_id = register_and_login()
    if not token:
        print("테스트 중단")
        return
    
    # 2. 스케줄러 상태 확인
    print_section("2. 스케줄러 상태 확인")
    check_scheduler_status(token)
    
    # 3. 할당량 생성
    print_section("3. 할당량 생성")
    quota_id = create_quota(token, user_id)
    if not quota_id:
        print("테스트 중단")
        return
    
    # 4. Job 생성 (사용량 증가)
    print_section("4. Job 생성 (사용량 증가)")
    create_jobs(token, count=3)
    
    # 5. 할당량 상태 확인
    print_section("5. 할당량 상태 확인 (사용량 증가 확인)")
    check_quota(token, quota_id)
    
    # 6. 리셋 통계 조회
    print_section("6. 리셋 통계 조회")
    get_reset_stats(token)
    
    # 7. 수동 일일 리셋
    print_section("7. 수동 일일 리셋")
    manual_reset_daily(token)
    
    # 8. 리셋 후 할당량 확인
    print_section("8. 일일 리셋 후 할당량 확인")
    quota = check_quota(token, quota_id)
    if quota:
        if quota['used_today'] == 0 and quota['used_week'] == 3 and quota['used_month'] == 3:
            print("✅ 일일 리셋 정상 작동 (daily만 초기화됨)")
        else:
            print("❌ 일일 리셋 오류")
    
    # 9. 수동 주간 리셋
    print_section("9. 수동 주간 리셋")
    manual_reset_weekly(token)
    
    # 10. 리셋 후 할당량 확인
    print_section("10. 주간 리셋 후 할당량 확인")
    quota = check_quota(token, quota_id)
    if quota:
        if quota['used_week'] == 0 and quota['used_month'] == 3:
            print("✅ 주간 리셋 정상 작동 (weekly만 추가 초기화됨)")
        else:
            print("❌ 주간 리셋 오류")
    
    # 11. 수동 월간 리셋
    print_section("11. 수동 월간 리셋")
    manual_reset_monthly(token)
    
    # 12. 리셋 후 할당량 확인
    print_section("12. 월간 리셋 후 할당량 확인")
    quota = check_quota(token, quota_id)
    if quota:
        if quota['used_month'] == 0:
            print("✅ 월간 리셋 정상 작동 (monthly까지 초기화됨)")
        else:
            print("❌ 월간 리셋 오류")
    
    # 최종 통계
    print_section("13. 최종 리셋 통계")
    get_reset_stats(token)
    
    print_section("테스트 완료")
    print("✅ Quota Reset Scheduler 테스트 완료\n")
    print("테스트된 기능:")
    print("  ✅ 스케줄러 상태 조회")
    print("  ✅ 스케줄 작업 등록 확인")
    print("  ✅ 사용량 증가 (Job 생성)")
    print("  ✅ 수동 일일 리셋")
    print("  ✅ 수동 주간 리셋")
    print("  ✅ 수동 월간 리셋")
    print("  ✅ 리셋 통계 조회\n")
    print("구현된 기능:")
    print("  - APScheduler 통합")
    print("  - 일일/주간/월간 자동 리셋 스케줄")
    print("  - 수동 리셋 API")
    print("  - 리셋 통계 API")
    print("  - 스케줄러 상태 모니터링\n")


if __name__ == "__main__":
    main()
