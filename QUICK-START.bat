@echo off
chcp 65001 > nul
cls
echo ========================================
echo  🎬 간단 실행 가이드
echo ========================================
echo.
echo 다음 순서대로 실행하세요:
echo.
echo 1단계: Docker 시작
echo    방법 1: start-docker.bat 더블클릭
echo    방법 2: 명령어 입력
echo.
echo 2단계: 10초 대기 (DB 초기화)
echo.
echo 3단계: 서버 시작
echo    방법 1: start-server.bat 더블클릭
echo    방법 2: 명령어 입력
echo.
echo ========================================
echo  빠른 명령어
echo ========================================
echo.
echo Docker 시작:
echo   cd /d c:\shorts ^&^& start-docker.bat
echo.
echo 서버 시작:
echo   cd /d c:\shorts ^&^& start-server.bat
echo.
echo 전체 중지:
echo   cd /d c:\shorts ^&^& STOP.bat
echo.
echo ========================================
echo.
echo 아무 키나 누르면 Docker를 시작합니다...
pause > nul

cd /d "%~dp0"
call start-docker.bat
