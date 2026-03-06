@echo off
REM Flower 모니터링 UI 실행 스크립트 (Windows)

cd /d C:\shorts\admin\backend

echo.
echo ========================================
echo 🌺 Starting Flower Monitoring UI...
echo ========================================
echo.
echo 📊 Flower will be available at:
echo    http://localhost:5555
echo.

REM PYTHONPATH 설정
set PYTHONPATH=%CD%

REM Flower 실행
.\venv\Scripts\celery.exe -A app.celery_app flower ^
    --port=5555 ^
    --broker=redis://localhost:6379/0

echo.
echo ❌ Flower stopped
echo.
pause
