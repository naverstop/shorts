@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🔍 개발환경 셋업 검증
echo ========================================
echo.

cd /d "%~dp0"

set "ERROR_COUNT=0"

echo [1/7] Python 검증...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다!
    set /a ERROR_COUNT+=1
) else (
    python --version
    echo ✅ Python 설치 확인
)
echo.

echo [2/7] Docker 검증...
docker --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Docker가 설치되지 않았습니다!
    set /a ERROR_COUNT+=1
) else (
    docker --version
    echo ✅ Docker 설치 확인
)
echo.

echo [3/7] Docker 실행 상태 검증...
docker ps > nul 2>&1
if errorlevel 1 (
    echo ❌ Docker가 실행되고 있지 않습니다!
    echo    Docker Desktop을 시작해주세요.
    set /a ERROR_COUNT+=1
) else (
    echo ✅ Docker 실행 중
)
echo.

echo [4/7] Docker 컨테이너 검증...
docker ps --filter "name=shorts" --format "{{.Names}}" | findstr shorts > nul
if errorlevel 1 (
    echo ⚠️  Shorts 컨테이너가 실행되지 않았습니다.
    echo    'start-docker.bat'를 실행해주세요.
    set /a ERROR_COUNT+=1
) else (
    echo ✅ Shorts 컨테이너 실행 중
    docker ps --filter "name=shorts" --format "  - {{.Names}} ({{.Status}})"
)
echo.

echo [5/7] Python 가상환경 검증...
if exist "admin\backend\venv" (
    echo ✅ 가상환경 존재
) else (
    echo ⚠️  가상환경이 없습니다.
    echo    'start-server.bat'를 실행하면 자동 생성됩니다.
    set /a ERROR_COUNT+=1
)
echo.

echo [6/7] Python 패키지 검증...
if exist "admin\backend\venv" (
    admin\backend\venv\Scripts\pip.exe list | findstr fastapi > nul 2>&1
    if errorlevel 1 (
        echo ⚠️  패키지가 설치되지 않았습니다.
        echo    'start-server.bat'를 실행하면 자동 설치됩니다.
        set /a ERROR_COUNT+=1
    ) else (
        echo ✅ 주요 패키지 설치 확인
        admin\backend\venv\Scripts\pip.exe list | findstr /i "fastapi uvicorn sqlalchemy redis" 2>nul
    )
) else (
    echo ⚠️  가상환경이 없어 패키지를 확인할 수 없습니다.
)
echo.

echo [7/7] 포트 사용 검증...
netstat -ano | findstr :8001 | findstr LISTENING > nul
if not errorlevel 1 (
    echo ⚠️  포트 8001이 이미 사용 중입니다.
    echo    서버가 이미 실행 중이거나 다른 프로그램이 사용 중입니다.
) else (
    echo ✅ 포트 8001 사용 가능
)
echo.

echo ========================================
echo  검증 결과
echo ========================================
if %ERROR_COUNT% EQU 0 (
    echo ✅ 모든 검증 통과!
    echo.
    echo 서버 시작: START.bat 또는 start-server.bat 실행
) else (
    echo ⚠️  %ERROR_COUNT%개의 문제가 발견되었습니다.
    echo.
    echo 해결 방법:
    echo  1. Docker Desktop 시작: start-docker.bat
    echo  2. 패키지 설치: start-server.bat (자동 설치)
    echo  3. 전체 시작: START.bat
)
echo ========================================
echo.
pause
