@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🧪 운영 점검 자동 실행 (E2E)
echo ========================================
echo.

cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"
set "SERVER_STARTED_BY_SCRIPT=0"
set "PYTHON_EXE="

echo [1/6] 🐳 Docker 인프라 확인/시작...
docker ps > nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Desktop이 실행 중이 아닙니다.
    exit /b 1
)

cd /d "%SCRIPT_DIR%docker"
docker compose up -d > nul 2>&1
if errorlevel 1 (
    docker-compose up -d > nul 2>&1
    if errorlevel 1 (
        echo ❌ Docker 컨테이너 시작 실패
        cd /d "%SCRIPT_DIR%"
        exit /b 1
    )
)
cd /d "%SCRIPT_DIR%"
echo ✅ Docker 인프라 준비 완료
echo.

echo [2/6] 🐍 Python 실행 경로 확인...
if exist "%SCRIPT_DIR%admin\backend\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%admin\backend\venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
)

if "%PYTHON_EXE%"=="" (
    echo ❌ Python 가상환경을 찾을 수 없습니다.
    echo    - %SCRIPT_DIR%.venv\Scripts\python.exe
    echo    - %SCRIPT_DIR%admin\backend\venv\Scripts\python.exe
    exit /b 1
)
echo ✅ Python: %PYTHON_EXE%
echo.

echo [3/6] 🚀 백엔드 서버 상태 확인...
netstat -ano | findstr :8001 | findstr LISTENING > nul
if errorlevel 1 (
    echo 서버가 실행 중이 아니므로 새로 시작합니다...
    start "AI-Shorts-Backend" /D "%SCRIPT_DIR%admin\backend" "%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8001
    set "SERVER_STARTED_BY_SCRIPT=1"
) else (
    echo ✅ 포트 8001 서버가 이미 실행 중입니다.
)
echo.

echo [4/6] ⏳ 서버 준비 대기...
"%PYTHON_EXE%" "%SCRIPT_DIR%scripts\wait_for_health.py" --url http://localhost:8001/health --retries 30 --interval 1 --timeout 2
if errorlevel 1 (
    echo ❌ 서버 준비 시간 초과 ^(health check 실패^)
    if "%SERVER_STARTED_BY_SCRIPT%"=="1" (
        echo 서버 프로세스를 종료합니다...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1
    )
    exit /b 1
)
echo ✅ 서버 준비 완료
echo.

echo [5/6] 🧾 E2E 점검 실행...
"%PYTHON_EXE%" "%SCRIPT_DIR%scripts\e2e_api_check.py" --base-url http://localhost:8001
set "E2E_EXIT=%ERRORLEVEL%"
echo.

echo [6/6] 🧹 정리...
if "%SERVER_STARTED_BY_SCRIPT%"=="1" (
    echo 스크립트가 시작한 서버를 종료합니다...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1
) else (
    echo 기존 서버는 유지합니다.
)
echo.

echo ========================================
if "%E2E_EXIT%"=="0" (
    echo  ✅ 운영 점검 통과
) else (
    echo  ❌ 운영 점검 실패
)
echo ========================================
echo.
exit /b %E2E_EXIT%
