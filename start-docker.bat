@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
cls
echo ========================================
echo  🐳 Docker 인프라 시작
echo ========================================
echo.

cd /d "%~dp0"
cd docker

echo [1/4] 🔍 Docker 상태 확인...
docker ps > nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker가 실행되고 있지 않습니다.
    echo.
    echo [2/4] 🚀 Docker Desktop 시작 중...
    
    REM Docker Desktop 경로 찾기
    set "DOCKER_PATH=C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if not exist "!DOCKER_PATH!" (
        echo ❌ Docker Desktop을 찾을 수 없습니다!
        echo 설치 경로: !DOCKER_PATH!
        echo Docker Desktop을 설치해주세요.
        pause
        exit /b 1
    )
    
    REM Docker Desktop 시작
    start "" "!DOCKER_PATH!"
    echo ✅ Docker Desktop 시작 명령 실행
    echo.
    
    echo [3/4] ⏳ Docker 초기화 대기 중...
    echo Docker가 완전히 시작될 때까지 대기합니다 (최대 60초)
    
    REM 60초 동안 5초마다 확인
    set /a counter=0
    :wait_docker
    timeout /t 5 /nobreak > nul
    docker ps > nul 2>&1
    if errorlevel 1 (
        set /a counter+=5
        if !counter! lss 60 (
            echo ... !counter!초 경과
            goto wait_docker
        ) else (
            echo ❌ Docker 시작 시간 초과! 수동으로 확인해주세요.
            pause
            exit /b 1
        )
    )
    echo ✅ Docker 시작 완료! (!counter!초 소요)
    echo.
) else (
    echo ✅ Docker가 이미 실행 중입니다.
    echo.
    echo [2/4] ♻️  기존 shorts 컨테이너 확인 및 정리...
    
    REM 기존 컨테이너 중지 및 삭제
    docker-compose down 2>nul
    if not errorlevel 1 (
        echo ✅ 기존 컨테이너 정리 완료
    )
    echo.
    
    echo [3/4] ⏳ 잠시 대기...
    timeout /t 2 /nobreak > nul
    echo.
)

echo [4/4] 🚀 컨테이너 시작...
echo (PostgreSQL 포트: 5433 사용 - 기존 5432 포트와 충돌 방지)
docker-compose up -d

if errorlevel 1 (
    echo.
    echo ❌ 컨테이너 시작 실패!
    echo.
    echo 추가 문제 해결:
    echo 1. 작업 관리자에서 postgres 프로세스 수동 종료
    echo 2. 또는 시스템 재부팅 후 재시도
    pause
    exit /b 1
)

echo.
echo ========================================
echo  🎉 인프라 시작 완료!
echo ========================================
echo  🐘 PostgreSQL:     localhost:5433
echo      - Database: shorts_db
echo      - User:     shorts_admin
echo      - Password: shorts_password_2026
echo      ⓘ  포트 5433 사용 (기존 PostgreSQL 충돌 방지)
echo.
echo  🔴 Redis:          localhost:6379
echo      - Password: redis_password_2026
echo.
echo  🌐 Adminer:        http://localhost:8080
echo      (PostgreSQL 관리 도구)
echo.
echo  🎛️  Redis Commander: http://localhost:8081
echo      (Redis 관리 도구)
echo ========================================
echo.
echo 컨테이너 상태 확인:
docker-compose ps
echo.
pause