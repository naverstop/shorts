"""
Celery Test Script

Celery Worker와 Task 실행 테스트
"""
import sys
import os

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

from app.celery_app import celery_app, debug_task
from app.tasks.cleanup import cleanup_old_logs, cleanup_temp_files
import time


def test_celery_connection():
    """Celery 연결 테스트"""
    print("=" * 60)
    print("🧪 Testing Celery Connection...")
    print("=" * 60)
    
    try:
        # Celery 상태 확인
        inspect = celery_app.control.inspect()
        
        print("\n📊 Celery Status:")
        print(f"  - Broker: {celery_app.conf.broker_url}")
        print(f"  - Backend: {celery_app.conf.result_backend}")
        
        # Active workers 확인
        active = inspect.active()
        if active:
            print(f"\n✅ Active Workers: {list(active.keys())}")
        else:
            print("\n⚠️  No active workers found")
            print("   Please start Celery worker first:")
            print("   > start-celery-worker.bat")
        
        # Registered tasks 확인
        registered = inspect.registered()
        if registered:
            print(f"\n📋 Registered Tasks:")
            for worker, tasks in registered.items():
                print(f"  Worker: {worker}")
                for task in sorted(tasks):
                    if task.startswith("app.tasks"):
                        print(f"    - {task}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Celery connection failed: {e}")
        return False


def test_debug_task():
    """디버그 태스크 실행 테스트"""
    print("\n" + "=" * 60)
    print("🧪 Testing Debug Task...")
    print("=" * 60)
    
    try:
        # 비동기 Task 실행
        result = debug_task.delay()
        print(f"\n✅ Task submitted: {result.id}")
        print("⏳ Waiting for result...")
        
        # 결과 대기 (최대 10초)
        task_result = result.get(timeout=10)
        print(f"✅ Task completed: {task_result}")
        
        return True
    
    except Exception as e:
        print(f"❌ Debug task failed: {e}")
        return False


def test_cleanup_task():
    """정리 태스크 테스트"""
    print("\n" + "=" * 60)
    print("🧪 Testing Cleanup Task...")
    print("=" * 60)
    
    try:
        # cleanup_temp_files Task 실행
        result = cleanup_temp_files.delay()
        print(f"\n✅ Cleanup task submitted: {result.id}")
        print("⏳ Waiting for result...")
        
        # 결과 대기 (최대 30초)
        task_result = result.get(timeout=30)
        print(f"✅ Cleanup completed:")
        print(f"   Status: {task_result.get('status')}")
        print(f"   Deleted: {task_result.get('deleted_files', 0)} files")
        print(f"   Freed: {task_result.get('freed_space_mb', 0)} MB")
        
        return True
    
    except Exception as e:
        print(f"❌ Cleanup task failed: {e}")
        return False


def test_scheduled_tasks():
    """스케줄된 태스크 확인"""
    print("\n" + "=" * 60)
    print("📅 Scheduled Tasks (Celery Beat):")
    print("=" * 60)
    
    for name, config in celery_app.conf.beat_schedule.items():
        print(f"\n📌 {name}:")
        print(f"   Task: {config['task']}")
        print(f"   Schedule: {config['schedule']}")


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 70)
    print("🚀 Celery Integration Test")
    print("=" * 70)
    
    # 1. Celery 연결 테스트
    if not test_celery_connection():
        print("\n⚠️  Celery worker가 실행되지 않았습니다.")
        print("   다음 명령으로 Worker를 먼저 시작해주세요:")
        print("   > start-celery-worker.bat")
        return
    
    # 2. 디버그 태스크 테스트
    test_debug_task()
    
    # 3. 정리 태스크 테스트
    test_cleanup_task()
    
    # 4. 스케줄된 태스크 확인
    test_scheduled_tasks()
    
    print("\n" + "=" * 70)
    print("✅ All Celery tests completed!")
    print("=" * 70)
    
    print("\n📚 Next Steps:")
    print("  1. Celery Worker: start-celery-worker.bat")
    print("  2. Celery Beat: start-celery-beat.bat")
    print("  3. Flower UI: start-celery-flower.bat → http://localhost:5555")


if __name__ == "__main__":
    main()
