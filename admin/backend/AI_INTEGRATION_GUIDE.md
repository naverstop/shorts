# AI Integration 설정 가이드

## 📋 개요

Sprint 7-8에서 구현된 AI Integration 시스템은 다음 기능을 제공합니다:

- **트렌드 분석**: YouTube Data API + Gemini AI를 활용한 트렌드 수집 및 분석
- **스크립트 생성**: Claude AI를 사용한 바이럴 숏폼 스크립트 자동 생성 (Hook-Body-CTA 구조)
- **Vector 임베딩**: OpenAI Embeddings를 통한 스크립트 의미 벡터화 (1536차원)
- **유사도 검색**: pgvector를 활용한 중복 스크립트 탐지 및 유사 콘텐츠 검색

## 🔑 API 키 설정

### 1. YouTube Data API

1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 프로젝트 생성 또는 선택
3. **API 및 서비스** > **라이브러리**로 이동
4. "YouTube Data API v3" 검색 후 활성화
5. **사용자 인증 정보** > **API 키 만들기**
6. 생성된 API 키를 복사

**쿼터 정보**:
- 무료: 하루 10,000 단위
- 트렌드 조회: 약 100 단위/요청
- 검색: 100 단위/요청

### 2. Gemini API (Google AI Studio)

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. **Get API Key** 클릭
3. API 키 생성
4. 생성된 키를 복사

**요금 정보**:
- Gemini 2.0 Flash: 무료 (일일 제한 있음)
- 프로덕션: 종량제 ($0.10/1M tokens)

### 3. Claude API (Anthropic)

1. [Anthropic Console](https://console.anthropic.com/) 접속
2. 계정 생성 또는 로그인
3. **API Keys** 섹션에서 키 생성
4. 생성된 키를 복사 (sk-ant-로 시작)

**요금 정보**:
- Claude 3.5 Sonnet: $3/1M input tokens, $15/1M output tokens
- 무료 크레딧: $5 (신규 가입)

### 4. OpenAI API

1. [OpenAI Platform](https://platform.openai.com/api-keys) 접속
2. **Create new secret key** 클릭
3. 키 이름 입력 후 생성
4. 생성된 키를 복사 (sk-로 시작)

**요금 정보**:
- text-embedding-3-small: $0.02/1M tokens
- 매우 저렴 (스크립트 1개당 약 $0.0001)

## ⚙️ .env 파일 설정

`admin/backend/.env` 파일을 열고 다음 API 키를 설정하세요:

```env
# YouTube Data API
YOUTUBE_API_KEY=your-actual-youtube-api-key-here

# Gemini API
GEMINI_API_KEY=your-actual-gemini-api-key-here

# Claude API (Anthropic)
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# OpenAI API
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

## 🗄️ 데이터베이스 마이그레이션

AI Integration 테이블(trends, scripts) 생성:

```powershell
cd C:\shorts\admin\backend
.\venv\Scripts\python.exe -m alembic upgrade head
```

**생성되는 테이블**:
- `trends`: YouTube/TikTok 트렌드 데이터, Gemini 분석 결과 (JSONB)
- `scripts`: AI 생성 스크립트, Vector(1536) 임베딩 (pgvector)

**인덱스**:
- trends: 9개 인덱스 (trend_score, source, category 등)
- scripts: 8개 인덱스 (embedding IVFFlat 포함)

## 🚀 서버 시작

```powershell
cd C:\shorts\admin\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

서버가 정상 실행되면:
- API 문서: http://localhost:8001/docs
- AI Integration 엔드포인트: http://localhost:8001/api/v1/trends, /scripts

## 🧪 테스트 실행

AI Integration 통합 테스트:

```powershell
cd C:\shorts\admin\backend
.\venv\Scripts\python.exe test_ai_integration.py
```

**테스트 시나리오**:
1. 테스트 사용자 등록/로그인
2. YouTube 트렌드 수집 (KR 지역, 10개)
3. AI 스크립트 생성 ("2026년 AI 트렌드" 주제)
4. Vector 유사도 검색 (threshold 0.85)
5. 내 스크립트 목록 조회

## 📚 API 사용 예제

### 트렌드 수집

```bash
curl -X POST "http://localhost:8001/api/v1/trends/collect" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "region_code": "KR",
    "category_id": null,
    "max_results": 10
  }'
```

**응답 예시**:
```json
{
  "message": "트렌드 수집 완료",
  "collected_count": 8,
  "duplicate_count": 2
}
```

### 스크립트 생성

```bash
curl -X POST "http://localhost:8001/api/v1/scripts" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "ChatGPT 활용법",
    "target_audience": "직장인",
    "platform": "youtube_shorts",
    "language": "ko",
    "duration": 30
  }'
```

**응답 예시**:
```json
{
  "id": 1,
  "title": "3초 만에 보고서 완성! ChatGPT 꿀팁",
  "hook": "보고서 3시간 걸렸던 당신! 이제 3분이면 됩니다",
  "body": "ChatGPT에게 [구체적인 지시문] 입력하면...",
  "cta": "이 영상이 도움됐다면 구독과 좋아요!",
  "ai_model": "claude-3-5-sonnet-20241022",
  "viral_potential": 85,
  "created_at": "2026-03-02T10:30:00Z"
}
```

### 유사 스크립트 검색

```bash
curl -X GET "http://localhost:8001/api/v1/scripts/1/similar?threshold=0.85&limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**응답 예시**:
```json
[
  {
    "script": {
      "id": 3,
      "title": "ChatGPT로 업무 자동화하기"
    },
    "similarity": 0.92
  },
  {
    "script": {
      "id": 5,
      "title": "AI로 생산성 10배 높이는 법"
    },
    "similarity": 0.87
  }
]
```

## 🔧 트러블슈팅

### pgvector 설치 오류

```bash
# Windows (PostgreSQL 16)
# pgvector는 PostgreSQL extension이므로 DB 서버에 설치 필요
# Docker를 사용하는 경우 이미 설치됨
```

### API 키 403 오류

- YouTube API: 쿼터 초과 확인 (Google Cloud Console > 할당량)
- Gemini API: 일일 요청 제한 확인
- Claude/OpenAI: 크레딧 잔액 확인

### 임베딩 벡터 차원 불일치

```python
# app/services/embedding_client.py
# text-embedding-3-small은 1536차원 고정
# app/models/script.py의 Vector(1536)와 일치해야 함
```

## 📊 비용 추정 (월별)

**개발 환경 (하루 100회 테스트)**:
- YouTube API: 무료 (쿼터 내)
- Gemini: 무료 (일일 제한 내)
- Claude: ~$3 (100회 * 30일 * $0.001)
- OpenAI Embedding: ~$0.30 (100회 * 30일 * $0.0001)
- **총액**: ~$3.30/월

**프로덕션 환경 (하루 1000회)**:
- Claude: ~$30/월
- OpenAI Embedding: ~$3/월
- YouTube/Gemini: Google Cloud 종량제
- **총액**: ~$35-50/월

## 🛠️ 개발 팁

### 로컬 테스트용 Mock 클라이언트

API 키 없이 테스트하려면:

```python
# app/services/youtube_client.py
class MockYouTubeClient:
    async def get_trending_videos(self, ...):
        return [{"id": "test1", "title": "Test Video"}]
```

### 벡터 검색 성능 최적화

```sql
-- IVFFlat 인덱스 파라미터 조정
CREATE INDEX scripts_embedding_idx ON scripts 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);  -- lists 값 조정 (기본: √rows)
```

## 📖 참고 자료

- [YouTube Data API 문서](https://developers.google.com/youtube/v3)
- [Gemini API 문서](https://ai.google.dev/docs)
- [Claude API 문서](https://docs.anthropic.com/claude/reference)
- [OpenAI API 문서](https://platform.openai.com/docs/api-reference)
- [pgvector GitHub](https://github.com/pgvector/pgvector)

---

**작성일**: 2026-03-02  
**버전**: v1.0  
**Sprint**: 7-8 (AI Integration)
