@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🚀 개발환경 자동 셋업
echo ========================================
echo.
echo 이 스크립트는 다음을 수행합니다:
echo  1. Docker Desktop 시작 (필요한 경우)
echo  2. Docker 컨테이너 시작
echo  3. Python 가상환경 생성
echo  4. 패키지 설치 및 정리
echo  5. 환경 검증
echo.
echo 계속하시겠습니까?
pause
echo.

cd /d "%~dp0"

echo ========================================
echo [1/5] Docker Desktop 시작
echo ========================================
docker ps > nul 2>&1
if errorlevel 1 (
    echo Docker Desktop을 시작합니다...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo 60초 대기 중...
    timeout /t 60 /nobreak > nul
) else (
    echo ✅ Docker가 이미 실행 중입니다.
)
echo.

echo ========================================
echo [2/5] Docker 컨테이너 시작
echo ========================================
cd docker
docker-compose down 2>nul
docker-compose up -d
if errorlevel 1 (
    echo ❌ Docker 컨테이너 시작 실패!
    pause
    exit /b 1
)
echo ✅ Docker 컨테이너 시작 완료
cd ..
echo.

echo ========================================
echo [3/5] Python 가상환경 생성
echo ========================================
cd admin\backend
if not exist "venv" (
    echo 가상환경을 생성합니다...
    python -m venv venv
    echo ✅ 가상환경 생성 완료
) else (
    echo ✅ 가상환경이 이미 존재합니다.
)
echo.

echo ========================================
echo [4/5] 패키지 설치 및 정리
echo ========================================
echo pip 업그레이드...
.\venv\Scripts\python.exe -m pip install --upgrade pip --quiet

echo.
echo 불필요한 패키지 제거...
.\venv\Scripts\pip.exe uninstall -y celery flower 2>nul

echo.
echo requirements.txt에서 패키지 설치...
.\venv\Scripts\pip.exe install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ 패키지 설치 실패!
    pause
    exit /b 1
)
echo ✅ 패키지 설치 완료
cd ..\..
echo.

echo ========================================
echo [5/5] 환경 검증
echo ========================================
echo PostgreSQL 연결 테스트...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 5433 -InformationLevel Quiet" > nul 2>&1
if errorlevel 1 (
    echo ⚠️  PostgreSQL 연결 실패 (포트 5433)
) else (
    echo ✅ PostgreSQL 연결 성공
)

echo Redis 연결 테스트...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet" > nul 2>&1
if errorlevel 1 (
    echo ⚠️  Redis 연결 실패 (포트 6379)
) else (
    echo ✅ Redis 연결 성공
)

echo FastAPI import 테스트...
cd admin\backend
.\venv\Scripts\python.exe -c "from app.main import app; print('✅ FastAPI import 성공')"
cd ..\..
echo.

echo ========================================
echo  ✅ 셋업 완료!
echo ========================================
echo.
echo 다음 명령어로 서버를 시작하세요:
echo.
echo  1. 빠른 시작:
echo     START.bat
echo.
echo  2. 개별 시작:
echo     start-docker.bat  (Docker만)
echo     start-server.bat  (서버만)
echo.
echo  3. 상태 확인:
echo     SETUP-CHECK.bat
echo.
echo ========================================
pause
