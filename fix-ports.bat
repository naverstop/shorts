@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🔧 포트 충돌 해결 도구
echo ========================================
echo.

cd /d "%~dp0"

echo 현재 사용 중인 포트 확인 중...
echo.

echo [PostgreSQL - 5433 (Docker용)]
netstat -ano | findstr :5433 | findstr LISTENING
if errorlevel 1 (
    echo ✅ 5433 포트 사용 가능
) else (
    echo ⚠️  5433 포트 사용 중
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5433 ^| findstr LISTENING') do (
        echo 프로세스 ID: %%a
        for /f "tokens=1" %%b in ('tasklist /fi "pid eq %%a" ^| findstr /v "Image"') do (
            echo 프로세스 이름: %%b
        )
    )
)
echo.

echo [PostgreSQL - 5432 (시스템용)]
netstat -ano | findstr :5432 | findstr LISTENING
if errorlevel 1 (
    echo ✅ 5432 포트 사용 없음
) else (
    echo ℹ️  5432 포트 사용 중 (시스템 PostgreSQL - 정상)
)
echo.

echo [Redis - 6379]
netstat -ano | findstr :6379 | findstr LISTENING
if errorlevel 1 (
    echo ✅ 6379 포트 사용 가능
) else (
    echo ⚠️  6379 포트 사용 중
)
echo.

echo [API Server - 8001]
netstat -ano | findstr :8001 | findstr LISTENING
if errorlevel 1 (
    echo ✅ 8001 포트 사용 가능
) else (
    echo ⚠️  8001 포트 사용 중
)
echo.

echo ========================================
echo  해결 방법
echo ========================================
echo.
echo ✅ PostgreSQL은 5433 포트 사용으로 설정됨
echo    기존 5432 포트와 충돌하지 않습니다.
echo.
echo 다른 포트 충돌 시:
echo   - Redis (6379): docker-compose down 후 재시작
echo   - API (8001): 실행 중인 Python 프로세스 종료
echo.
pause
