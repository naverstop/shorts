@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🔍 개발 환경 진단
echo ========================================
echo.

cd /d "%~dp0"
echo 현재 디렉토리: %CD%
echo.

echo [1] 배치 파일 확인
dir /b *.bat
echo.

echo [2] Python 버전
python --version
echo.

echo [3] Docker 상태
docker --version
docker ps > nul 2>&1
if errorlevel 1 (
    echo ❌ Docker가 실행되고 있지 않습니다!
) else (
    echo ✅ Docker 실행 중
)
echo.

echo [4] 프로젝트 구조
tree /F /A | findstr /v "node_modules .git venv __pycache__" | Select-Object -First 30
echo.

echo [5] Docker 컨테이너 상태
docker ps -a --filter "name=shorts" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo ========================================
echo  진단 완료
echo ========================================
pause
