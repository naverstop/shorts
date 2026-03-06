@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🛑 모든 서비스 중지
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 🚀 FastAPI 서버 프로세스 종료...
REM 포트 8001을 사용하는 프로세스 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo 프로세스 ID %%a 종료 중...
    taskkill /F /PID %%a 2>nul
)

REM Python/uvicorn 프로세스 종료
tasklist | findstr /i "uvicorn" > nul
if not errorlevel 1 (
    echo uvicorn 프로세스 종료 중...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq AI Shorts*" 2>nul
)
echo ✅ 서버 프로세스 종료 완료

echo.
echo [2/3] 🐳 Docker 컨테이너 중지...
cd docker
docker-compose down
if errorlevel 1 (
    echo ⚠️  Docker 컨테이너 중지에 문제가 있을 수 있습니다.
) else (
    echo ✅ Docker 컨테이너 중지 완료
)
cd ..

echo.
echo [3/3] 🔍 최종 확인...
netstat -ano | findstr :8001 > nul
if errorlevel 1 (
    echo ✅ 포트 8001 해제됨
) else (
    echo ⚠️  포트 8001이 여전히 사용 중입니다.
    echo    수동으로 프로세스를 종료해야 할 수 있습니다.
)

echo.
echo ========================================
echo  ✅ 서비스 중지 완료!
echo ========================================
echo.
pause
