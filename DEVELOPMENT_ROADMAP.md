# 🚀 Phase 1 개발 로드맵 (Week 7-16)

**작성일**: 2026년 3월 2일  
**현재 주차**: Week 7 (42% 완료)  
**목표**: Backend 완성 + Android Agent 개발 + E2E 검증

---

## 📋 주차별 상세 작업 계획

## Week 7 (현재) - Backend 안정화

### 🎯 목표
- 서버 이슈 해결 및 안정화
- WebSocket 기초 구현
- 다음 Sprint 준비

### ✅ 작업 목록

#### Day 1 (월요일) - 긴급 이슈 해결
- [ ] **서버 시작 이슈 디버깅**
  ```bash
  # 로그 확인
  cd c:\shorts\admin\backend
  .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
  
  # 예상 원인
  1. import 오류
  2. DATABASE_URL 문제
  3. 순환 참조
  ```
  
- [ ] **문제 해결 및 검증**
  - 로그 분석
  - 오류 수정
  - 정상 시작 확인
  - http://localhost:8001/docs 접속 확인

#### Day 2-3 (화수) - WebSocket 기본 구현
- [ ] **WebSocket 엔드포인트 생성**
  ```python
  # app/routes/websocket.py 생성
  from fastapi import WebSocket, WebSocketDisconnect
  from typing import List
  
  class ConnectionManager:
      def __init__(self):
          self.active_connections: List[WebSocket] = []
      
      async def connect(self, websocket: WebSocket):
          await websocket.accept()
          self.active_connections.append(websocket)
      
      def disconnect(self, websocket: WebSocket):
          self.active_connections.remove(websocket)
      
      async def broadcast(self, message: dict):
          for connection in self.active_connections:
              await connection.send_json(message)
  
  manager = ConnectionManager()
  
  @router.websocket("/ws/agents")
  async def websocket_agent_status(websocket: WebSocket):
      await manager.connect(websocket)
      try:
          while True:
              data = await websocket.receive_text()
              await manager.broadcast({"type": "agent_update", "data": data})
      except WebSocketDisconnect:
          manager.disconnect(websocket)
  ```

- [ ] **Agent Heartbeat WebSocket 통합**
  ```python
  # app/routes/agents.py 수정
  @router.post("/{agent_id}/heartbeat")
  async def agent_heartbeat(
      agent_id: int,
      heartbeat: AgentHeartbeat,
      db: AsyncSession = Depends(get_db)
  ):
      # ... 기존 로직 ...
      
      # WebSocket 브로드캐스트 추가
      await manager.broadcast({
          "type": "heartbeat",
          "agent_id": agent_id,
          "status": agent.status,
          "timestamp": datetime.now().isoformat()
      })
      
      return {"status": "ok"}
  ```

- [ ] **테스트**
  ```python
  # tests/test_websocket.py
  from fastapi.testclient import TestClient
  
  def test_websocket_connection():
      with client.websocket_connect("/ws/agents") as websocket:
          data = websocket.receive_json()
          assert "type" in data
  ```

#### Day 4-5 (목금) - Celery 기본 설정
- [ ] **Celery 패키지 설치**
  ```bash
  # requirements.txt 추가
  celery[redis]==5.3.4
  flower==2.0.1  # Celery 모니터링 UI
  ```

- [ ] **Celery 구성 파일 생성**
  ```python
  # app/celery_app.py
  from celery import Celery
  from app.config import settings
  
  celery_app = Celery(
      "shorts_admin",
      broker=settings.REDIS_URL,
      backend=settings.REDIS_URL
  )
  
  celery_app.conf.update(
      task_serializer="json",
      accept_content=["json"],
      result_serializer="json",
      timezone="Asia/Seoul",
      enable_utc=True,
  )
  
  # Autodiscover tasks
  celery_app.autodiscover_tasks(["app.tasks"])
  ```

- [ ] **첫 번째 Task 구현**
  ```python
  # app/tasks/cleanup.py
  from app.celery_app import celery_app
  from app.database import async_session
  from sqlalchemy import delete
  from datetime import datetime, timedelta
  
  @celery_app.task
  def cleanup_old_logs():
      """90일 이상 오래된 로그 삭제"""
      async with async_session() as db:
          cutoff_date = datetime.now() - timedelta(days=90)
          await db.execute(
              delete(Log).where(Log.created_at < cutoff_date)
          )
          await db.commit()
      return {"status": "ok", "cutoff_date": cutoff_date.isoformat()}
  ```

- [ ] **Celery Beat 스케줄러 설정**
  ```python
  # app/celery_app.py 추가
  from celery.schedules import crontab
  
  celery_app.conf.beat_schedule = {
      "cleanup-old-logs": {
          "task": "app.tasks.cleanup.cleanup_old_logs",
          "schedule": crontab(hour=2, minute=0),  # 매일 새벽 2시
      },
  }
  ```

- [ ] **Celery Worker 실행 스크립트**
  ```powershell
  # start-celery-worker.bat
  @echo off
  cd /d C:\shorts\admin\backend
  .\venv\Scripts\celery.exe -A app.celery_app worker -l info --pool=solo
  ```

- [ ] **Flower 모니터링 실행**
  ```powershell
  # start-celery-flower.bat
  @echo off
  cd /d C:\shorts\admin\backend
  .\venv\Scripts\celery.exe -A app.celery_app flower --port=5555
  ```

### 📊 Week 7 성공 지표
- [x] 서버 정상 시작 (Exit Code 0)
- [x] WebSocket 연결 테스트 통과
- [x] Celery Worker 실행 확인
- [x] 첫 번째 Task 실행 성공

---

## Week 8 - 플랫폼 인증 시스템

### 🎯 목표
- 플랫폼 인증 관리 API 완성
- OAuth2 플로우 구현
- WebSocket 완성

### ✅ 작업 목록

#### Day 1-2 (월화) - Credential CRUD API
- [ ] **Schemas 정의**
  ```python
  # app/schemas.py 추가
  class CredentialCreate(BaseModel):
      platform_id: int
      credential_name: str
      credentials: dict
      is_default: bool = False
  
  class CredentialResponse(BaseModel):
      id: int
      user_id: int
      platform_id: int
      platform: PlatformResponse
      credential_name: str
      is_default: bool
      status: str
      last_validated: Optional[datetime]
      created_at: datetime
  ```

- [ ] **라우터 구현**
  ```python
  # app/routes/credentials.py 생성
  @router.post("/credentials", response_model=CredentialResponse)
  async def create_credential(
      credential: CredentialCreate,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db)
  ):
      # 1. 인증 정보 암호화
      encrypted = encrypt_credentials(credential.credentials)
      
      # 2. DB 저장
      db_credential = UserPlatformCredential(
          user_id=current_user.id,
          platform_id=credential.platform_id,
          credential_name=credential.credential_name,
          credentials=encrypted,
          is_default=credential.is_default
      )
      
      # 3. Channel 자동 생성
      await create_channels_for_credential(db, current_user.id, db_credential.id)
      
      return db_credential
  ```

- [ ] **Channel 자동 생성 로직**
  ```python
  # app/services/channel_service.py
  async def create_channels_for_credential(
      db: AsyncSession,
      user_id: int,
      credential_id: int
  ):
      # 해당 User의 모든 Agent 조회
      result = await db.execute(
          select(Agent).where(Agent.user_id == user_id)
      )
      agents = result.scalars().all()
      
      # Agent별 Channel 생성
      for agent in agents:
          channel = Channel(
              agent_id=agent.id,
              user_credential_id=credential_id,
              platform=credential.platform.platform_code,
              status="active"
          )
          db.add(channel)
      
      await db.commit()
  ```

#### Day 3-4 (수목) - OAuth2 플로우 (YouTube)
- [ ] **OAuth2 라이브러리 설치**
  ```bash
  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
  ```

- [ ] **OAuth2 인증 시작**
  ```python
  # app/routes/oauth.py
  from google_auth_oauthlib.flow import Flow
  
  @router.get("/oauth/youtube/authorize")
  async def youtube_oauth_authorize(
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db)
  ):
      flow = Flow.from_client_secrets_file(
          "client_secrets.json",
          scopes=["https://www.googleapis.com/auth/youtube.upload"],
          redirect_uri="http://localhost:8001/api/v1/oauth/youtube/callback"
      )
      
      authorization_url, state = flow.authorization_url(
          access_type="offline",
          include_granted_scopes="true"
      )
      
      # state를 Redis에 임시 저장 (10분 TTL)
      await redis.setex(f"oauth:state:{state}", 600, current_user.id)
      
      return {"authorization_url": authorization_url}
  ```

- [ ] **OAuth2 콜백 처리**
  ```python
  @router.get("/oauth/youtube/callback")
  async def youtube_oauth_callback(
      code: str,
      state: str,
      db: AsyncSession = Depends(get_db)
  ):
      # state 검증
      user_id = await redis.get(f"oauth:state:{state}")
      if not user_id:
          raise HTTPException(status_code=400, detail="Invalid state")
      
      # Access Token 교환
      flow = Flow.from_client_secrets_file(...)
      flow.fetch_token(code=code)
      credentials = flow.credentials
      
      # DB에 저장
      db_credential = UserPlatformCredential(
          user_id=int(user_id),
          platform_id=1,  # YouTube
          credentials={
              "access_token": credentials.token,
              "refresh_token": credentials.refresh_token,
              "token_uri": credentials.token_uri,
              "client_id": credentials.client_id,
              "client_secret": credentials.client_secret,
          },
          status="active"
      )
      db.add(db_credential)
      await db.commit()
      
      return {"status": "success", "credential_id": db_credential.id}
  ```

#### Day 5 (금) - WebSocket 완성
- [ ] **Job 상태 변경 시 WebSocket 브로드캐스트**
- [ ] **Agent 상태 변경 시 WebSocket 브로드캐스트**
- [ ] **WebSocket 재연결 로직**
- [ ] **통합 테스트**

### 📊 Week 8 성공 지표
- [x] Credential CRUD 5개 API 완성
- [x] YouTube OAuth2 플로우 동작
- [x] Channel 자동 생성 확인
- [x] WebSocket 실시간 업데이트 동작

---

## Week 9-10 - 업로드 제한 시스템 + Android 착수

### 🎯 목표
- 플랫폼 업로드 제한 관리 완성
- Android Agent 프로젝트 초기화
- AI API 통합 시작

### ✅ Week 9 작업

#### Backend: 업로드 제한 시스템 (3일)
- [ ] **UploadLimitService 구현**
  ```python
  # app/services/upload_limit_service.py
  class UploadLimitService:
      def __init__(self, redis_client, db_session):
          self.redis = redis_client
          self.db = db_session
      
      async def check_upload_allowed(
          self,
          channel_id: int,
          platform: str
      ) -> dict:
          """업로드 가능 여부 체크"""
          limit = await self.get_platform_limit(platform)
          
          # 일일 제한 체크
          daily_key = f"upload:daily:{channel_id}:{date.today().strftime('%Y%m%d')}"
          daily_count = await self.redis.get(daily_key) or 0
          if int(daily_count) >= limit.daily_upload_limit:
              return {
                  "allowed": False,
                  "reason": "daily_limit_exceeded",
                  "retry_at": self.get_next_day()
              }
          
          # 시간당 제한 체크
          hourly_key = f"upload:hourly:{channel_id}:{datetime.now().strftime('%Y%m%d%H')}"
          hourly_count = await self.redis.get(hourly_key) or 0
          if int(hourly_count) >= limit.hourly_upload_limit:
              return {
                  "allowed": False,
                  "reason": "hourly_limit_exceeded",
                  "retry_at": self.get_next_hour()
              }
          
          # 최소 간격 체크
          last_upload = await self.redis.get(f"upload:last:{channel_id}")
          if last_upload:
              elapsed = datetime.now() - datetime.fromisoformat(last_upload)
              if elapsed.total_seconds() < limit.min_upload_interval_minutes * 60:
                  return {
                      "allowed": False,
                      "reason": "min_interval_not_met",
                      "retry_at": last_upload + timedelta(minutes=limit.min_upload_interval_minutes)
                  }
          
          return {"allowed": True}
      
      async def record_upload(self, channel_id: int, platform: str, file_size_mb: float):
          """업로드 기록"""
          today = date.today().strftime('%Y%m%d')
          current_hour = datetime.now().strftime('%Y%m%d%H')
          
          # 일일 카운트 증가
          daily_key = f"upload:daily:{channel_id}:{today}"
          await self.redis.incr(daily_key)
          await self.redis.expire(daily_key, 86400)  # 24시간
          
          # 시간당 카운트 증가
          hourly_key = f"upload:hourly:{channel_id}:{current_hour}"
          await self.redis.incr(hourly_key)
          await self.redis.expire(hourly_key, 3600)  # 1시간
          
          # 마지막 업로드 시간 기록
          await self.redis.setex(
              f"upload:last:{channel_id}",
              3600,
              datetime.now().isoformat()
          )
          
          # DB에 기록
          tracking = UploadTracking(
              channel_id=channel_id,
              upload_date=date.today(),
              platform=platform,
              video_count=1,
              total_size_mb=file_size_mb
          )
          self.db.add(tracking)
          await self.db.commit()
  ```

- [ ] **업로드 제한 API**
  ```python
  @router.post("/uploads/check")
  async def check_upload_limit(
      channel_id: int,
      platform: str,
      db: AsyncSession = Depends(get_db)
  ):
      service = UploadLimitService(redis, db)
      result = await service.check_upload_allowed(channel_id, platform)
      return result
  
  @router.get("/channels/{channel_id}/quota")
  async def get_channel_quota(
      channel_id: int,
      db: AsyncSession = Depends(get_db)
  ):
      """채널별 잔여 쿼터 조회"""
      # Redis에서 오늘 업로드 수 조회
      # 플랫폼 제한과 비교하여 잔여량 반환
      pass
  ```

#### Android: 프로젝트 초기화 (2일)
- [ ] **React Native 프로젝트 생성**
  ```bash
  npx react-native@latest init ShortsAgent
  cd ShortsAgent
  ```

- [ ] **필수 라이브러리 설치**
  ```bash
  npm install @react-native-async-storage/async-storage
  npm install axios
  npm install react-native-fs
  npm install @react-native-community/netinfo
  ```

- [ ] **프로젝트 구조 생성**
  ```
  ShortsAgent/
  ├── android/
  │   └── app/
  │       └── src/
  │           └── main/
  │               └── java/
  │                   └── com/
  │                       └── shortsagent/
  │                           ├── FFmpegModule.kt
  │                           └── AccessibilityModule.kt
  ├── src/
  │   ├── api/
  │   │   └── adminClient.ts
  │   ├── screens/
  │   │   ├── LoginScreen.tsx
  │   │   └── DashboardScreen.tsx
  │   ├── services/
  │   │   ├── HeartbeatService.ts
  │   │   └── JobPollingService.ts
  │   └── App.tsx
  └── package.json
  ```

### ✅ Week 10 작업

#### AI API 통합: Gemini (3일)
- [ ] **Gemini API 클라이언트**
  ```python
  # app/services/ai/gemini_client.py
  import google.generativeai as genai
  from app.config import settings
  
  genai.configure(api_key=settings.GEMINI_API_KEY)
  
  class GeminiClient:
      def __init__(self):
          self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
      
      async def analyze_trend(self, video_data: dict) -> dict:
          """트렌드 분석"""
          prompt = f"""
          다음 유튜브 영상 데이터를 분석해주세요:
          
          제목: {video_data['title']}
          조회수: {video_data['views']}
          좋아요: {video_data['likes']}
          
          분석 항목:
          1. 주요 키워드 추출 (5개)
          2. 타겟 연령대
          3. 콘텐츠 카테고리
          4. 바이럴 요소 분석
          5. 추천 스크립트 방향
          
          JSON 형식으로 응답해주세요.
          """
          
          response = await self.model.generate_content_async(prompt)
          return json.loads(response.text)
  ```

- [ ] **트렌드 수집 Celery Task**
  ```python
  # app/tasks/trend_collection.py
  from app.celery_app import celery_app
  from app.services.ai.gemini_client import GeminiClient
  from googleapiclient.discovery import build
  
  @celery_app.task
  def collect_youtube_trends():
      """YouTube 트렌드 수집 (1시간마다)"""
      youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
      
      # 인기 동영상 조회
      request = youtube.videos().list(
          part="snippet,statistics",
          chart="mostPopular",
          regionCode="KR",
          maxResults=50
      )
      response = request.execute()
      
      # Gemini로 분석
      gemini = GeminiClient()
      for video in response["items"]:
          analysis = await gemini.analyze_trend({
              "title": video["snippet"]["title"],
              "views": video["statistics"]["viewCount"],
              "likes": video["statistics"]["likeCount"]
          })
          
          # DB 저장
          trend = Trend(
              platform="youtube",
              video_id=video["id"],
              title=video["snippet"]["title"],
              analysis=analysis
          )
          db.add(trend)
      
      await db.commit()
  ```

#### Android: API 통신 구현 (2일)
- [ ] **Admin API 클라이언트**
  ```typescript
  // src/api/adminClient.ts
  import axios from 'axios';
  import AsyncStorage from '@react-native-async-storage/async-storage';
  
  const API_BASE_URL = 'http://192.168.1.100:8001/api/v1';
  
  export class AdminClient {
    private apiKey: string;
    
    async initialize() {
      this.apiKey = await AsyncStorage.getItem('api_key');
    }
    
    async sendHeartbeat(agentId: number) {
      return axios.post(
        `${API_BASE_URL}/agents/${agentId}/heartbeat`,
        {
          status: 'idle',
          disk_usage_percent: 45
        },
        {
          headers: { 'X-API-Key': this.apiKey }
        }
      );
    }
    
    async getAvailableJob(agentId: number) {
      const response = await axios.get(
        `${API_BASE_URL}/jobs/available`,
        {
          params: { agent_id: agentId },
          headers: { 'X-API-Key': this.apiKey }
        }
      );
      return response.data;
    }
  }
  ```

### 📊 Week 9-10 성공 지표
- [x] 업로드 제한 시스템 동작 (Redis + PostgreSQL)
- [x] Gemini API 트렌드 분석 실행
- [x] Android Agent API 통신 성공
- [x] Heartbeat 30초마다 전송 확인

---

## Week 11-12 - Android 렌더링 + Claude/TTS 통합

### 🎯 목표
- FFmpeg 영상 렌더링
- Claude API 스크립트 생성
- Google Cloud TTS 통합

### ✅ 작업 목록 (상세 생략, 계획서 참조)
- [ ] FFmpeg Mobile 라이브러리 빌드
- [ ] Native Module (Kotlin) 구현
- [ ] React Native 브릿지
- [ ] Claude API 클라이언트
- [ ] TTS 음성 다운로드
- [ ] 자막 동기화 (SRT)

---

## Week 13-14 - Android 자동 업로드 + Frontend 시작

### 🎯 목표
- Accessibility Service 업로드 자동화
- Admin Dashboard 기본 구조

### ✅ 작업 목록 (상세 생략)
- [ ] Accessibility Service 권한
- [ ] 플랫폼별 업로드 시퀀스
- [ ] React Dashboard 프로젝트
- [ ] Agent 모니터링 UI

---

## Week 15-16 - 통합 테스트 & 배포 준비

### 🎯 목표
- 1대 Agent E2E 검증
- 10대 통합 테스트
- 문서화 및 배포

### ✅ 작업 목록
- [ ] E2E 테스트 시나리오 작성
- [ ] 10대 동시 실행 테스트
- [ ] 성능 최적화
- [ ] API 문서화 완성
- [ ] 배포 매뉴얼 작성

---

## 📊 전체 일정 요약

| 주차 | 백엔드 | Android | AI/기타 | 완성도 |
|------|--------|---------|---------|--------|
| Week 7 | WebSocket, Celery | - | - | 50% |
| Week 8 | 플랫폼 인증 | - | - | 60% |
| Week 9 | 업로드 제한 | 프로젝트 초기화 | Gemini | 65% |
| Week 10 | - | API 통신 | Gemini Task | 70% |
| Week 11 | - | 렌더링 구현 | Claude, TTS | 78% |
| Week 12 | - | 렌더링 완성 | Vector DB | 85% |
| Week 13 | - | 자동 업로드 | - | 90% |
| Week 14 | Frontend 시작 | 통합 테스트 | - | 93% |
| Week 15 | Frontend 완성 | E2E 테스트 | - | 97% |
| Week 16 | 배포 준비 | 문서화 | - | 100% |

---

## 🔥 즉시 착수 항목 (Backlog)

### P0 (긴급)
1. [ ] 서버 시작 이슈 해결
2. [ ] WebSocket 기본 구현
3. [ ] Celery Worker 셋업

### P1 (높음)
4. [ ] 플랫폼 인증 API (OAuth2)
5. [ ] 업로드 제한 시스템
6. [ ] Android 프로젝트 초기화

### P2 (중간)
7. [ ] Gemini API 통합
8. [ ] Claude API 통합
9. [ ] Frontend 프로젝트 시작

---

**작성자**: GitHub Copilot  
**업데이트**: 2026년 3월 2일  
**다음 리뷰**: Week 9 (2026년 3월 16일)
