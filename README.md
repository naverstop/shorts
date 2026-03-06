# AI 쇼츠 자동 생성 시스템 - 개발 가이드

## 🚀 빠른 시작

### 1. 필수 요구사항
- **Python 3.11+** 설치
- **Docker Desktop** 설치 및 실행
- **Git** (선택사항)

### 2. 개발환경 셋업 (처음 설치 시)

```cmd
# 개발환경 자동 셋업 (처음 한 번만)
SETUP.bat

# 또는 환경 검증만
SETUP-CHECK.bat
```

**SETUP.bat가 수행하는 작업:**
- Docker Desktop 자동 시작
- Docker 컨테이너 생성 및 시작
- Python 가상환경 생성
- 패키지 자동 설치 및 정리
- 환경 검증

### 3. 원클릭 실행 (셋업 완료 후)

```cmd
# 모든 서비스 한 번에 시작
START.bat
```

**START.bat가 수행하는 작업:**
1. ✅ Docker 인프라 시작 (PostgreSQL, Redis)
2. ✅ Python 가상환경 확인/생성
3. ✅ 패키지 설치 확인
4. ✅ 환경 설정 확인 (.env)
5. ✅ FastAPI 서버 시작 (포트 8001)

**중요:**
- 서버가 **이 창에서 실행**됩니다 (새 창 열림 없음)
- **Ctrl+C**를 눌러 서버를 종료할 수 있습니다
- 서버 로그를 **실시간으로** 확인할 수 있습니다
- 서버 실행 후 브라우저에서 http://localhost:8001 접속

### 4. 개별 실행

```cmd
# Docker만 시작
start-docker.bat

# 서버만 시작 (Docker가 실행 중이어야 함)
start-server.bat

# 모든 서비스 중지
STOP.bat

# 환경 검증
SETUP-CHECK.bat
```

### 5. 문제 해결

개발환경 구성에 문제가 있다면:

```cmd
# 1. 환경 상태 확인
SETUP-CHECK.bat

# 2. 자동 수정 및 재설치
SETUP.bat

# 3. 포트 충돌 확인
fix-ports.bat
```

## 📡 접속 정보

| 서비스 | URL | 설명 |
|--------|-----|------|
| **API Server** | http://localhost:8001 | FastAPI 메인 서버 |
| **API 문서** | http://localhost:8001/docs | Swagger UI |
| **Health Check** | http://localhost:8001/health | 서버 상태 확인 |
| **Adminer** | http://localhost:8080 | PostgreSQL 관리 |
| **Redis Commander** | http://localhost:8081 | Redis 관리 |

### 데이터베이스 접속 정보 (Adminer)

**Adminer에서 접속할 때 (http://localhost:8080):**
- **System**: PostgreSQL
- **Server**: postgres
- **Username**: shorts_admin
- **Password**: shorts_password_2026
- **Database**: shorts_db

**외부 도구(DBeaver, pgAdmin)에서 접속할 때:**
- **Host**: localhost
- **Port**: 5433
- **Username**: shorts_admin
- **Password**: shorts_password_2026
- **Database**: shorts_db

**⚠️ 중요:** 
- Adminer(웹)에서는 Server에 **postgres** 입력 (Docker 내부 이름)
- 외부 도구에서는 **localhost:5433** 사용

## 🗂️ 프로젝트 구조

```
c:\shorts\
├── START.bat              # 원클릭 실행
├── STOP.bat               # 모든 서비스 중지
├── start-docker.bat       # Docker만 시작
├── start-server.bat       # 서버만 시작
├── admin/
│   ├── backend/
│   │   ├── venv/          # Python 가상환경 (자동 생성)
│   │   ├── app/
│   │   │   ├── main.py    # FastAPI 메인 앱
│   │   │   └── config.py  # 설정 파일
│   │   ├── requirements.txt
│   │   ├── .env           # 환경 변수 (자동 생성)
│   │   └── logs/          # 로그 파일
│   └── frontend/          # React (추후 개발)
├── docker/
│   ├── docker-compose.yml
│   └── init-db.sql
└── 작업계획서_v1.0.md     # 전체 개발 계획서
```

## 🔧 개발 환경 설정

### Python 가상환경 수동 생성 (필요시)

```cmd
cd admin\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일을 편집하여 API 키를 설정하세요:

```env
# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key-here

# Claude API
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Google Cloud (TTS, Translation)
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-key.json
```

## 🧪 API 테스트

서버 시작 후 브라우저에서:

```
http://localhost:8001/docs
```

자동 생성된 Swagger UI에서 모든 API를 테스트할 수 있습니다.

### 테스트 실행 (권장 가상환경)

프로젝트는 실행 스크립트 기준으로 `admin\backend\venv`를 사용합니다.

```cmd
cd admin\backend
venv\Scripts\activate
python -m pytest tests\test_main.py -q
```

## 🐞 문제 해결

### Docker 관련
```cmd
# Docker Desktop이 자동으로 시작되지 않는 경우
# 1. Docker Desktop 수동 실행
"C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 2. Docker 상태 확인
docker ps

# 3. 컨테이너 재시작
cd docker
docker-compose restart

# 4. 완전히 재시작
docker-compose down
docker-compose up -d
```

**Docker Desktop 경로가 다른 경우:**
`start-docker.bat` 파일을 열어서 `DOCKER_PATH` 변수를 수정하세요.

### Python 패키지 오류
```cmd
cd admin\backend
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 포트 충돌
프로젝트에서 사용하는 포트:
- **5433번 포트: PostgreSQL** (기존 5432와 충돌 방지)
- 6379번 포트: Redis
- 8001번 포트: FastAPI 서버
- 8080번 포트: Adminer
- 8081번 포트: Redis Commander

**기존 PostgreSQL과 함께 사용 가능:**
- 시스템 PostgreSQL: localhost:5432
- Docker PostgreSQL: localhost:5433
- 두 데이터베이스를 동시에 사용할 수 있습니다.

## 📚 다음 단계

1. ✅ 개발 환경 구성 완료
2. 🔜 데이터베이스 테이블 생성 (Alembic Migration)
3. 🔜 인증 시스템 구현 (JWT)
4. 🔜 Agent 관리 API 구현
5. 🔜 Job 관리 API 구현

자세한 내용은 `작업계획서_v1.0.md`를 참조하세요.

## 🆘 도움말

문제가 발생하면:
1. `STOP.bat`로 모든 서비스 중지
2. Docker Desktop 재시작
3. `START.bat`로 다시 시작

그래도 안 되면 로그 확인:
- FastAPI: `admin\backend\logs\app.log`
- Docker: `docker-compose logs`
