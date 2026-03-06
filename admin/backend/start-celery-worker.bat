@echo off
REM Celery Worker 실행 스크립트 (Windows)

cd /d C:\shorts\admin\backend

echo.
echo ========================================
echo 🚀 Starting Celery Worker...
echo ========================================
echo.

REM PYTHONPATH 설정
set PYTHONPATH=%CD%

REM Celery Worker 실행
.\venv\Scripts\celery.exe -A app.celery_app worker ^
    -l info ^
    --pool=solo ^
    --concurrency=4 ^
    --max-tasks-per-child=100 ^
    --logfile=logs/celery_worker.log

echo.
echo ❌ Celery Worker stopped
echo.
pause
