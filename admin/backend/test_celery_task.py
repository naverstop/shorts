"""
Celery Task 실행 테스트
"""
import sys
import time
import os

# UTF-8 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

# Redis URL 설정
os.environ['REDIS_URL'] = 'redis://:redis_password_2026@localhost:6379/0'

from app.tasks.cleanup import cleanup_temp_files

print("=" * 60)
print("Celery Task 실행 테스트")
print("=" * 60)

# Task 제출
result = cleanup_temp_files.delay()
print(f"\n✅ Task 제출 완료")
print(f"   Task ID: {result.id}")

# 잠시 대기
time.sleep(3)

# 상태 확인
print(f"\n📊 Task 상태: {result.status}")

# 결과 확인 (최대 10초 대기)
try:
    if result.ready():
        task_result = result.get()
        print(f"✅ Task 완료: {task_result}")
    else:
        print("⏳ Task가 아직 처리 중입니다...")
        print("   10초간 결과를 기다립니다...")
        task_result = result.get(timeout=10)
        print(f"✅ Task 완료: {task_result}")
except Exception as e:
    print(f"❌ Task 실행 오류: {e}")

print("\n" + "=" * 60)
