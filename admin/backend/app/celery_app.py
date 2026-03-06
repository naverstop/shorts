"""
Celery Application Configuration
"""
from celery import Celery
from celery.schedules import crontab
import os

# Redis URL 설정 (비밀번호 포함)
REDIS_URL = os.getenv("REDIS_URL", "redis://:redis_password_2026@localhost:6379/0")

# Celery 앱 생성
celery_app = Celery(
    "shorts_admin",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.cleanup", "app.tasks.trends", "app.tasks.stats"]
)

# Celery 설정
celery_app.conf.update(
    # 직렬화 설정
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 시간대 설정
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # Task 실행 설정
    task_track_started=True,
    task_time_limit=3600,  # 1시간 타임아웃
    task_soft_time_limit=3300,  # 55분 소프트 타임아웃
    
    # Worker 설정
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Result backend 설정
    result_expires=86400,  # 결과 24시간 보관
    result_backend_transport_options={
        "master_name": "mymaster"
    },
    
    # Task 라우팅 (모든 Task를 기본 celery 큐로)
    # Phase 2에서 큐 분리 시 재활성화
    # task_routes={
    #     "app.tasks.cleanup.*": {"queue": "cleanup"},
    #     "app.tasks.trends.*": {"queue": "trends"},
    #     "app.tasks.stats.*": {"queue": "stats"},
    # },
)

# Celery Beat 스케줄 설정
celery_app.conf.beat_schedule = {
    # 로그 정리 (매일 새벽 2시)
    "cleanup-old-logs": {
        "task": "app.tasks.cleanup.cleanup_old_logs",
        "schedule": crontab(hour=2, minute=0),
    },
    
    # 임시 파일 정리 (매일 새벽 3시)
    "cleanup-temp-files": {
        "task": "app.tasks.cleanup.cleanup_temp_files",
        "schedule": crontab(hour=3, minute=0),
    },
    
    # 오래된 Job 아카이빙 (매일 새벽 4시)
    "archive-old-jobs": {
        "task": "app.tasks.cleanup.archive_old_jobs",
        "schedule": crontab(hour=4, minute=0),
    },
    
}

ENABLE_PHASE15_TASKS = os.getenv("ENABLE_PHASE15_TASKS", "false").lower() in {"1", "true", "yes", "on"}

if ENABLE_PHASE15_TASKS:
    celery_app.conf.beat_schedule.update(
        {
            "collect-youtube-trends": {
                "task": "app.tasks.trends.collect_youtube_trends",
                "schedule": crontab(minute=0),
            },
            "collect-tiktok-trends": {
                "task": "app.tasks.trends.collect_tiktok_trends",
                "schedule": crontab(minute=30),
            },
            "sync-video-stats": {
                "task": "app.tasks.stats.sync_video_stats",
                "schedule": crontab(hour="*/6", minute=0),
            },
            "analyze-video-performance": {
                "task": "app.tasks.stats.analyze_video_performance",
                "schedule": crontab(hour=3, minute=30),
            },
            "check-agent-disk-usage": {
                "task": "app.tasks.cleanup.check_agent_disk_usage",
                "schedule": crontab(hour=4, minute=30),
            },
        }
    )

# Celery 시그널 핸들러
@celery_app.task(bind=True)
def debug_task(self):
    """디버그용 테스트 태스크"""
    print(f"Request: {self.request!r}")
    return "Debug task completed"
