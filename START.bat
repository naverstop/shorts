@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🎬 AI 쇼츠 자동 생성 시스템 - 올인원 실행
echo ========================================
echo.

cd /d "%~dp0"

REM 배치 파일 디렉토리 저장
set "SCRIPT_DIR=%~dp0"

REM ===========================================
REM [단계 1] Docker 인프라 시작
REM ===========================================
echo [단계 1/5] 🐳 Docker 인프라 시작
echo.
call "%SCRIPT_DIR%start-docker.bat"
if errorlevel 1 (
    echo ❌ Docker 인프라 시작 실패!
    pause
    exit /b 1
)

echo.
echo ⏳ 데이터베이스 초기화 대기 중 (10초)...
timeout /t 10 /nobreak > nul

REM ===========================================
REM [단계 2] Python 가상환경 확인
REM ===========================================
cd /d "%SCRIPT_DIR%admin\backend"

echo.
echo [단계 2/5] 🔧 Python 가상환경 확인
echo.

if not exist "venv" (
    echo 가상환경을 생성합니다...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 가상환경 생성 실패! Python이 설치되어 있는지 확인하세요.
        cd /d "%SCRIPT_DIR%"
        pause
        exit /b 1
    )
    echo ✅ 가상환경 생성 완료!
) else (
    echo ✅ 가상환경이 이미 존재합니다.
)

REM ===========================================
REM [단계 3] 패키지 설치 확인
REM ===========================================
echo.
echo [단계 3/5] 📦 Python 패키지 설치 확인
echo.

venv\Scripts\pip.exe list 2>nul | findstr fastapi > nul
if errorlevel 1 (
    echo 패키지를 설치합니다. 시간이 걸릴 수 있습니다...
    venv\Scripts\pip.exe install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ❌ 패키지 설치 실패!
        cd /d "%SCRIPT_DIR%"
        pause
        exit /b 1
    )
    echo ✅ 패키지 설치 완료!
) else (
    echo ✅ 필수 패키지가 이미 설치되어 있습니다.
)

REM ===========================================
REM [단계 4] 환경 설정 확인
REM ===========================================
echo.
echo [단계 4/5] ⚙️  환경 설정 확인
echo.

if not exist ".env" (
    echo .env 파일이 없습니다. .env.example을 복사합니다...
    copy .env.example .env > nul
    echo ⚠️  .env 파일을 생성했습니다.
)
echo ✅ .env 파일 확인 완료

REM 필요한 디렉토리 생성
if not exist "logs" mkdir logs
if not exist "storage\uploads" mkdir storage\uploads
if not exist "storage\videos" mkdir storage\videos
if not exist "storage\temp" mkdir storage\temp

REM ===========================================
REM [단계 5] FastAPI 서버 시작
REM ===========================================
echo.
echo [단계 5/5] 🚀 FastAPI 서버 시작
echo.
echo ========================================
echo  ✅ 모든 서비스가 준비되었습니다!
echo ========================================
echo.
echo 📡 서비스 접속 정보:
echo  - API Server:  http://localhost:8001
echo  - API Docs:    http://localhost:8001/docs
echo  - Health:      http://localhost:8001/health
echo  - Adminer:     http://localhost:8080
echo  - Redis UI:    http://localhost:8081
echo ========================================
echo.
echo 💡 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

REM 작업 디렉토리를 확실히 admin\backend로 설정
cd /d "%SCRIPT_DIR%admin\backend"

REM FastAPI 서버 실행 (포그라운드) - 상대 경로 사용
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

REM 서버 종료 시
echo.
echo 서버가 종료되었습니다.
cd /d "%SCRIPT_DIR%"
pause
