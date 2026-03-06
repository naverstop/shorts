@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🚀 AI 쇼츠 자동 생성 시스템 - 개발 서버
echo ========================================
echo.

REM 색상 설정
color 0A

REM 프로젝트 루트로 이동
cd /d "%~dp0"
cd admin\backend

echo [1/6] 📁 작업 디렉토리 확인...
echo 현재 디렉토리: %CD%
echo.

REM 가상환경 확인 및 생성
if not exist "venv" (
    echo [2/6] 🔧 Python 가상환경 생성 중...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 가상환경 생성 실패! Python이 설치되어 있는지 확인하세요.
        pause
        exit /b 1
    )
    echo ✅ 가상환경 생성 완료!
    echo.
) else (
    echo [2/6] ✅ 가상환경이 이미 존재합니다.
    echo.
)

REM 의존성 설치 확인
echo [3/6] 📦 Python 패키지 설치 확인...
venv\Scripts\pip.exe list | findstr fastapi > nul
if errorlevel 1 (
    echo 패키지를 설치합니다. 시간이 걸릴 수 있습니다...
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 패키지 설치 실패!
        pause
        exit /b 1
    )
    echo ✅ 패키지 설치 완료!
) else (
    echo ✅ 필수 패키지가 이미 설치되어 있습니다.
)
echo.

REM .env 파일 확인
echo [4/6] ⚙️  환경 설정 확인...
if not exist ".env" (
    echo .env 파일이 없습니다. .env.example을 복사합니다...
    copy .env.example .env > nul
    echo ⚠️  .env 파일을 생성했습니다. API 키를 설정해주세요!
) else (
    echo ✅ .env 파일이 존재합니다.
)
echo.

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs
if not exist "storage\uploads" mkdir storage\uploads
if not exist "storage\videos" mkdir storage\videos
if not exist "storage\temp" mkdir storage\temp

echo [5/6] 🎬 FastAPI 서버 시작...
echo.
echo ========================================
echo  서버 정보
echo ========================================
echo  📡 API Server: http://localhost:8001
echo  📚 API Docs:   http://localhost:8001/docs
echo  🔍 Health:     http://localhost:8001/health
echo ========================================
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

REM FastAPI 서버 실행 (가상환경의 Python 직접 사용)
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

REM 서버 종료 시
echo.
echo 서버가 종료되었습니다.
pause
