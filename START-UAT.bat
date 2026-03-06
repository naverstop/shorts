@echo off
REM 실사용자 테스트 환경 자동 시작 스크립트

echo ========================================
echo  실사용자 테스트 환경 시작
echo ========================================
echo.

REM 1. Docker 서비스 확인 및 시작
echo [1/7] Docker 서비스 확인...
docker ps >nul 2>&1
if errorlevel 1 (
    echo   ❌ Docker가 실행 중이 아닙니다. Docker Desktop을 시작해주세요.
    pause
    exit /b 1
)
echo   ✓ Docker 실행 중

REM 2. PostgreSQL 시작
echo [2/7] PostgreSQL 시작...
call start-docker.bat
timeout /t 5 >nul
echo   ✓ PostgreSQL 준비 완료

REM 3. Redis 시작 (이미 실행 중이면 skip)
echo [3/7] Redis 시작...
docker ps | findstr redis >nul
if errorlevel 1 (
    docker run -d -p 6379:6379 --name redis redis:7-alpine >nul 2>&1
    if errorlevel 1 (
        echo   ⚠ Redis 시작 실패 또는 이미 존재함
    ) else (
        echo   ✓ Redis 시작 완료
    )
) else (
    echo   ✓ Redis 이미 실행 중
)

REM 4. Backend 서버 시작 (백그라운드)
echo [4/7] Backend 서버 시작...
start "Backend Server" cmd /k "cd admin\backend && call .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 >nul
echo   ✓ Backend 서버 시작됨 (포트 8001)

REM 5. Celery Worker 시작 (백그라운드)
echo [5/7] Celery Worker 시작...
start "Celery Worker" cmd /k "cd admin\backend && call .venv\Scripts\activate && celery -A app.celery_app worker -l info"
timeout /t 2 >nul
echo   ✓ Celery Worker 시작됨

REM 6. Celery Beat 시작 (백그라운드)
echo [6/7] Celery Beat 시작...
start "Celery Beat" cmd /k "cd admin\backend && call .venv\Scripts\activate && celery -A app.celery_app beat -l info"
timeout /t 2 >nul
echo   ✓ Celery Beat 시작됨

REM 7. Frontend 서빙 (백그라운드)
echo [7/7] Frontend 빌드 및 서빙...
start "Frontend Build" cmd /k "cd admin\frontend && npm run build && npx serve -s dist -p 3000"
timeout /t 3 >nul
echo   ✓ Frontend 빌드 시작 (포트 3000)

echo.
echo ========================================
echo  ✅ 실사용자 테스트 환경 준비 완료
echo ========================================
echo.
echo 서비스 URL:
echo   - Frontend:  http://localhost:3000
echo   - Backend:   http://localhost:8001
echo   - API Docs:  http://localhost:8001/docs
echo   - Health:    http://localhost:8001/health
echo.
echo 선택적 서비스 (수동 시작):
echo   - Celery Flower: start-celery-flower.bat
echo.
echo 모든 창을 닫으면 서비스가 종료됩니다.
echo.
pause
