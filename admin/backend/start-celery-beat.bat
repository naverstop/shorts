@echo off
REM Celery Beat 스케줄러 실행 스크립트 (Windows)

cd /d C:\shorts\admin\backend

echo.
echo ========================================
echo ⏰ Starting Celery Beat Scheduler...
echo ========================================
echo.

REM PYTHONPATH 설정
set PYTHONPATH=%CD%

REM Celery Beat 실행
.\venv\Scripts\celery.exe -A app.celery_app beat ^
    -l info ^
    --logfile=logs/celery_beat.log

echo.
echo ❌ Celery Beat stopped
echo.
pause
