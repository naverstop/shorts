# 시스템 아키텍처 재설계 제안서

**작성일**: 2026년 3월 4일  
**버전**: 2.0  
**목적**: SIM 카드 기반 멀티 계정 관리 시스템

---

## 🚨 현재 구조의 한계

### 사용자 요구사항
1. **1명 사용자가 1~100개 SIM 운영**
2. **SIM 1개당 여러 플랫폼 서비스 매칭**
3. **SIM별 독립적인 Agent 동작**
4. **관리자의 통합/개별 Order 지시**
5. **이 구조가 전제되어야 함**

### 현재 설계의 문제
```
User → Agent (N개)
User → Credential (N개)
User → Quota (플랫폼당 1개) ← 문제!

❌ SIM 개념 없음
❌ Agent와 Credential 매핑 불명확
❌ 계정별 독립적 할당량 불가
❌ SIM별 Job 할당 불가
```

### 실제 운영 시나리오 (불가능)
```
사용자 A가 SIM 3개 운영:
  SIM 1 (010-1111-1111) → Agent 1 (Galaxy S21)
    ├─ YouTube 계정 A (게임 채널) → 일일 10개
    ├─ TikTok 계정 A (게임) → 일일 5개
    └─ Instagram 계정 A (게임) → 일일 3개
  
  SIM 2 (010-2222-2222) → Agent 2 (Galaxy S22)
    ├─ YouTube 계정 B (음악 채널) → 일일 5개
    └─ TikTok 계정 B (음악) → 일일 10개
  
  SIM 3 (010-3333-3333) → Agent 3 (iPhone 14)
    └─ YouTube 계정 C (뉴스 채널) → 일일 20개

→ 현재 구조로는 이런 매핑 불가능!
```

---

## ✅ 새로운 아키텍처 설계

### 핵심 개념: SIM 중심 설계

```
┌─────────────────────────────────────────────────────────────┐
│                         User (사용자)                         │
│                    testadmin@example.com                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ 1:N (최대 100개)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    SIM Card (전화번호)                       │
│              ┌──────────┬──────────┬──────────┐             │
│              │  SIM 1   │  SIM 2   │  SIM 3   │             │
│              │ 010-1111 │ 010-2222 │ 010-3333 │             │
│              └────┬─────┴────┬─────┴────┬─────┘             │
└───────────────────┼──────────┼──────────┼───────────────────┘
                    │          │          │
                    │ 1:1      │ 1:1      │ 1:1
                    ↓          ↓          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Agent (Android 기기)                        │
│         ┌────────────┬────────────┬────────────┐            │
│         │  Agent 1   │  Agent 2   │  Agent 3   │            │
│         │ Galaxy S21 │ Galaxy S22 │  iPhone 14 │            │
│         │  Online    │  Online    │  Offline   │            │
│         └─────┬──────┴─────┬──────┴─────┬──────┘            │
└───────────────┼────────────┼────────────┼───────────────────┘
                │            │            │
                │ 1:N        │ 1:N        │ 1:N
                ↓            ↓            ↓
┌─────────────────────────────────────────────────────────────┐
│           Platform Account (플랫폼별 계정)                   │
│   ┌─────────────┬─────────────┬─────────────┐               │
│   │ YouTube A   │ YouTube B   │ YouTube C   │               │
│   │ TikTok A    │ TikTok B    │             │               │
│   │ Instagram A │             │             │               │
│   └──────┬──────┴──────┬──────┴──────┬──────┘               │
└──────────┼─────────────┼─────────────┼──────────────────────┘
           │ 1:1         │ 1:1         │ 1:1
           ↓             ↓             ↓
┌─────────────────────────────────────────────────────────────┐
│              Upload Quota (업로드 할당량)                    │
│   ┌──────────────┬──────────────┬──────────────┐            │
│   │ YouTube A:   │ YouTube B:   │ YouTube C:   │            │
│   │ 일일 3/10    │ 일일 0/5     │ 일일 15/20   │            │
│   │ 주간 15/50   │ 주간 8/30    │ 주간 60/100  │            │
│   │ ✅ 사용 가능 │ ✅ 사용 가능 │ ⚠️  80% 사용 │            │
│   └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 새로운 DB 스키마

### 1. **sim_cards** 테이블 (NEW!)
```sql
CREATE TABLE sim_cards (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- SIM 카드 정보
  sim_number VARCHAR(20) UNIQUE NOT NULL,  -- 전화번호 (010-1234-5678)
  sim_iccid VARCHAR(50),                   -- SIM 카드 ICCID (고유번호)
  carrier VARCHAR(50),                     -- 통신사 (SKT, KT, LGU+)
  
  -- Google 계정 정보 (1 SIM = 1 Google Account)
  google_account_email VARCHAR(100),       -- Google 계정 이메일
  google_account_status VARCHAR(20) DEFAULT 'active',  -- active, banned, suspended
  
  -- 메타데이터
  nickname VARCHAR(100),                   -- 별칭 (예: "게임채널용 SIM")
  notes TEXT,                              -- 메모
  status VARCHAR(20) DEFAULT 'active',     -- active, inactive, banned
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_sim_user (user_id),
  INDEX idx_sim_number (sim_number),
  INDEX idx_sim_status (status)
);
```

### 2. **agents** 테이블 (수정)
```sql
CREATE TABLE agents (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_id INTEGER UNIQUE REFERENCES sim_cards(id) ON DELETE SET NULL,  -- NEW! 1:1 매핑
  
  -- 기기 정보
  device_name VARCHAR(100) NOT NULL,       -- Galaxy S21
  device_id VARCHAR(100) UNIQUE NOT NULL,  -- 기기 고유 ID
  device_model VARCHAR(50),                -- SM-G991N
  
  -- 연결 정보
  api_key VARCHAR(128) UNIQUE NOT NULL,
  status VARCHAR(20) DEFAULT 'offline',    -- online, offline, maintenance
  last_heartbeat TIMESTAMPTZ,
  ip_address INET,
  
  -- Android 정보
  android_version VARCHAR(20),
  apk_version VARCHAR(20),
  
  -- 자원 정보
  disk_usage_percent INTEGER,
  last_disk_cleanup TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_agent_user (user_id),
  INDEX idx_agent_sim (sim_id),
  INDEX idx_agent_status (status),
  
  -- 제약: SIM과 Agent는 1:1 매핑
  CONSTRAINT fk_agent_sim FOREIGN KEY (sim_id) REFERENCES sim_cards(id)
);
```

### 3. **platform_accounts** 테이블 (Credential 대체)
```sql
CREATE TABLE platform_accounts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_id INTEGER NOT NULL REFERENCES sim_cards(id) ON DELETE CASCADE,  -- SIM 매핑!
  platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
  
  -- 계정 정보
  account_name VARCHAR(100),               -- "게임채널 A"
  account_identifier VARCHAR(100),         -- 채널 ID, 사용자명 등
  
  -- 인증 정보 (암호화됨)
  credentials JSONB NOT NULL,              -- OAuth tokens, cookies 등
  
  -- 상태 정보
  status VARCHAR(20) DEFAULT 'active',     -- active, expired, banned, invalid
  last_validated TIMESTAMPTZ,              -- 마지막 검증 시각
  last_used TIMESTAMPTZ,                   -- 마지막 사용 시각
  ban_detected_at TIMESTAMPTZ,             -- Ban 감지 시각
  ban_reason TEXT,                         -- Ban 사유
  
  -- 메타데이터
  is_primary BOOLEAN DEFAULT false,        -- SIM 내에서 주 계정 여부
  notes TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_account_user (user_id),
  INDEX idx_account_sim (sim_id),
  INDEX idx_account_platform (platform_id),
  INDEX idx_account_status (status),
  
  -- 제약: (sim, platform)별로 여러 계정 가능
  UNIQUE (sim_id, platform_id, account_name)
);
```

### 4. **upload_quotas** 테이블 (수정)
```sql
CREATE TABLE upload_quotas (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  platform_account_id INTEGER UNIQUE NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,  -- 계정별!
  
  -- 제한 설정
  daily_limit INTEGER DEFAULT 0,
  weekly_limit INTEGER DEFAULT 0,
  monthly_limit INTEGER DEFAULT 0,
  
  -- 사용량
  used_today INTEGER DEFAULT 0,
  used_week INTEGER DEFAULT 0,
  used_month INTEGER DEFAULT 0,
  
  -- 리셋 타임스탬프
  last_daily_reset TIMESTAMPTZ DEFAULT NOW(),
  last_weekly_reset TIMESTAMPTZ DEFAULT NOW(),
  last_monthly_reset TIMESTAMPTZ DEFAULT NOW(),
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_quota_account (platform_account_id),
  
  -- 제약: 계정당 1개 할당량
  CONSTRAINT fk_quota_account FOREIGN KEY (platform_account_id) REFERENCES platform_accounts(id)
);
```

### 5. **jobs** 테이블 (수정)
```sql
CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  
  -- 할당 정보 (선택적)
  target_sim_id INTEGER REFERENCES sim_cards(id),           -- 특정 SIM에 할당
  target_agent_id INTEGER REFERENCES agents(id),            -- 특정 Agent에 할당 (더 구체적)
  assigned_agent_id INTEGER REFERENCES agents(id),          -- 실제 처리 Agent
  
  target_platform_id INTEGER NOT NULL REFERENCES platforms(id),  -- 타겟 플랫폼
  
  -- Job 정보
  title TEXT,
  script TEXT,
  status VARCHAR(20) DEFAULT 'pending',    -- pending, assigned, rendering, uploading, completed, failed, cancelled
  priority INTEGER DEFAULT 5,
  retry_count INTEGER DEFAULT 0,
  
  -- 결과
  video_path TEXT,
  video_url TEXT,
  error_message TEXT,
  
  -- 타임스탬프
  created_at TIMESTAMPTZ DEFAULT NOW(),
  assigned_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  
  INDEX idx_job_user (user_id),
  INDEX idx_job_sim (target_sim_id),
  INDEX idx_job_agent (assigned_agent_id),
  INDEX idx_job_status (status),
  INDEX idx_job_priority (priority),
  
  -- Job 할당 로직:
  -- 1. target_agent_id 지정 → 해당 Agent만 처리 가능
  -- 2. target_sim_id 지정 → 해당 SIM의 Agent만 처리 가능
  -- 3. 둘 다 NULL → 사용자의 모든 Agent 처리 가능
);
```

### 6. **platform_account_stats** 테이블 (NEW! - 모니터링)
```sql
CREATE TABLE platform_account_stats (
  id SERIAL PRIMARY KEY,
  platform_account_id INTEGER NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
  
  -- 업로드 통계
  total_uploads INTEGER DEFAULT 0,
  successful_uploads INTEGER DEFAULT 0,
  failed_uploads INTEGER DEFAULT 0,
  
  -- 마지막 활동
  last_upload_at TIMESTAMPTZ,
  last_successful_upload_at TIMESTAMPTZ,
  last_failed_upload_at TIMESTAMPTZ,
  
  -- 에러 추적
  consecutive_failures INTEGER DEFAULT 0,
  last_error_message TEXT,
  
  -- 상태 변경 이력
  status_changes JSONB,  -- [{timestamp, old_status, new_status, reason}]
  
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_stats_account (platform_account_id)
);
```

---

## 🔄 데이터 흐름

### 시나리오 1: 신규 SIM 등록
```
1. 관리자가 Dashboard에서 "SIM 추가" 클릭
2. 입력:
   - 전화번호: 010-1234-5678
   - 통신사: SKT
   - Google 계정: game.channel.a@gmail.com
   - 별칭: "게임채널용 SIM"
3. Backend: sim_cards 테이블에 INSERT
4. SIM ID 생성 (예: sim_id=5)
```

### 시나리오 2: Agent 등록 (Android 앱)
```
1. Android 폰에서 App 실행
2. "Register" 버튼 클릭
3. 입력:
   - Device Name: Galaxy S21
   - Backend URL: http://192.168.1.100:8001
   - SIM 선택: 010-1234-5678 (sim_id=5)
4. Backend: agents 테이블에 INSERT
   - sim_id=5 (1:1 매핑)
   - status='online'
5. Agent ID 생성 (예: agent_id=10)
```

### 시나리오 3: YouTube 계정 등록 (OAuth)
```
1. Dashboard → "플랫폼 관리" → YouTube 카드 클릭
2. "계정 추가" 버튼 클릭
3. SIM 선택: 010-1234-5678 (sim_id=5)
4. 계정 이름: "게임채널 A"
5. "OAuth 시작" → Google 로그인
6. Backend: platform_accounts 테이블에 INSERT
   - sim_id=5
   - platform_id=1 (YouTube)
   - account_name="게임채널 A"
   - credentials={access_token, refresh_token}
7. Account ID 생성 (예: account_id=20)
```

### 시나리오 4: 할당량 설정
```
1. Dashboard → YouTube 카드 → "게임채널 A" 선택
2. "할당량 설정" 버튼 클릭
3. 입력:
   - 일일: 10
   - 주간: 50
   - 월간: 200
4. Backend: upload_quotas 테이블에 INSERT
   - platform_account_id=20
   - daily_limit=10
```

### 시나리오 5: Job 생성 (통합 - 모든 Agent)
```
1. Dashboard → "Job 관리" → "Job 생성"
2. 입력:
   - 플랫폼: YouTube
   - 제목: "게임 공략 영상"
   - 스크립트: "..."
   - 할당: "모든 Agent" (target_sim_id=NULL, target_agent_id=NULL)
3. Backend: jobs 테이블에 INSERT
   - user_id=1
   - target_sim_id=NULL
   - target_agent_id=NULL
   - status='pending'
4. 모든 온라인 Agent가 처리 가능
```

### 시나리오 6: Job 생성 (개별 - 특정 SIM만)
```
1. Dashboard → "Job 관리" → "Job 생성"
2. 입력:
   - 플랫폼: YouTube
   - 제목: "게임 공략 영상"
   - 할당: "SIM 010-1234-5678" (target_sim_id=5)
3. Backend: jobs 테이블에 INSERT
   - target_sim_id=5
4. sim_id=5의 Agent(agent_id=10)만 처리 가능
```

### 시나리오 7: Job 처리
```
1. Agent가 /api/v1/jobs/next 호출
   - agent_id=10, sim_id=5
2. Backend Job 할당 로직:
   - target_agent_id=10 → 매칭!
   - OR target_sim_id=5 → 매칭!
   - OR 둘 다 NULL → 매칭!
3. Job 반환 (job_id=100)
4. Agent가 영상 생성 → 업로드
5. Backend: platform_accounts에서 sim_id=5의 YouTube 계정 조회
6. 해당 계정의 credentials로 업로드
7. upload_quotas 업데이트 (used_today++)
```

---

## 🎨 새로운 UI 구조

### Dashboard → SIM 관리 (NEW!)
```
┌─────────────────────────────────────────────────────────────┐
│                    📱 SIM 카드 관리                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [+ SIM 추가]  [🔄 새로고침]  [📊 통계]                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ SIM 1: 010-1111-1111 (SKT) ✅ 정상                 │    │
│  │ 별칭: 게임채널용 SIM                                │    │
│  │ Google 계정: game.channel.a@gmail.com              │    │
│  │ 연결 Agent: Galaxy S21 (Agent#10) 🟢 Online        │    │
│  │ 등록 계정: YouTube 1개, TikTok 1개, Instagram 1개  │    │
│  │ [상세보기] [수정] [비활성화]                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ SIM 2: 010-2222-2222 (KT) ⚠️  Agent 미연결        │    │
│  │ 별칭: 음악채널용 SIM                                │    │
│  │ Google 계정: music.channel.b@gmail.com             │    │
│  │ 연결 Agent: 없음 (Agent 등록 필요)                 │    │
│  │ 등록 계정: YouTube 1개, TikTok 1개                 │    │
│  │ [Agent 등록 가이드] [수정]                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ SIM 3: 010-3333-3333 (LGU+) ⛔ Ban 됨              │    │
│  │ 별칭: 뉴스채널용 SIM                                │    │
│  │ Google 계정: news.channel.c@gmail.com              │    │
│  │ 연결 Agent: iPhone 14 (Agent#15) 🔴 Offline        │    │
│  │ 등록 계정: YouTube 1개 (Ban 됨)                    │    │
│  │ Ban 감지: 2024-03-02 15:30 (YouTube 정책 위반)    │    │
│  │ [Ban 복구 가이드] [새 계정 등록]                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard → 플랫폼 관리 (수정)
```
┌─────────────────────────────────────────────────────────────┐
│           📺 YouTube (1개 플랫폼, 3개 SIM, 3개 계정)        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 🔐 등록 계정 현황: 3개                                       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 계정 1: 게임채널 A                                │       │
│  │ 📱 SIM: 010-1111-1111 (게임채널용 SIM)           │       │
│  │ 🤖 Agent: Galaxy S21 (Agent#10) 🟢 Online        │       │
│  │ ✅ 정상 | 마지막 검증: 2시간 전                  │       │
│  │ 📊 할당량: 일일 3/10, 주간 15/50, 월간 60/200    │       │
│  │ 📈 통계: 총 120개 업로드 (성공 118, 실패 2)      │       │
│  │ [상세보기] [할당량 수정] [인증 갱신]              │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 계정 2: 음악채널 B                                │       │
│  │ 📱 SIM: 010-2222-2222 (음악채널용 SIM)           │       │
│  │ 🤖 Agent: 미연결 ⚠️                               │       │
│  │ ⚠️  Agent 미연결 (영상 업로드 불가)              │       │
│  │ 📊 할당량: 일일 0/5, 주간 8/30, 월간 50/150      │       │
│  │ [Agent 연결 가이드]                               │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 계정 3: 뉴스채널 C                                │       │
│  │ 📱 SIM: 010-3333-3333 (뉴스채널용 SIM)           │       │
│  │ 🤖 Agent: iPhone 14 (Agent#15) 🔴 Offline        │       │
│  │ ⛔ Ban 됨 (2024-03-02 15:30)                     │       │
│  │ 사유: YouTube 정책 위반 (스팸 의심)              │       │
│  │ 📊 할당량: 사용 불가                              │       │
│  │ [Ban 복구 가이드] [새 계정 등록]                  │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│  [+ 계정 추가 (OAuth)] [📊 전체 통계]                        │
│                                                              │
│ ⚙️  플랫폼 제한 사항                                         │
│  시간당: 10개 | 일일: 100개 | 최대 길이: 60초               │
│  최대 파일: 256MB | 지원 포맷: MP4, MOV                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard → Job 생성 (수정)
```
┌─────────────────────────────────────────────────────────────┐
│                       🎬 Job 생성                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  플랫폼: [YouTube ▼]                                         │
│                                                              │
│  할당 방식:                                                  │
│    ◉ 모든 Agent (가능한 Agent가 자동 처리)                  │
│    ○ 특정 SIM 지정                                          │
│       └─ SIM: [010-1111-1111 (게임채널용) ▼]               │
│    ○ 특정 Agent 지정                                        │
│       └─ Agent: [Galaxy S21 (Agent#10) ▼]                  │
│                                                              │
│  제목: [게임 공략 영상 - 던전 100층 클리어]                  │
│                                                              │
│  스크립트:                                                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 안녕하세요! 오늘은 던전 100층을 클리어하는 방법을  │     │
│  │ 알려드리겠습니다...                                │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  우선순위: [5 (보통) ▼]                                      │
│                                                              │
│  [Job 생성] [취소]                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 마이그레이션 계획

### Phase 1: DB 스키마 마이그레이션 (1-2일)
1. **신규 테이블 생성**:
   - `sim_cards`
   - `platform_accounts` (credential 대체)
   - `platform_account_stats`

2. **기존 테이블 수정**:
   - `agents`: `sim_id` 컬럼 추가
   - `upload_quotas`: `platform_account_id` 컬럼 추가
   - `jobs`: `target_sim_id`, `target_agent_id` 컬럼 추가

3. **데이터 마이그레이션**:
   - 기존 `user_platform_credentials` → `platform_accounts`
   - 기존 `upload_quotas` → 새 구조로 변환
   - 기존 `agents` → SIM 매핑 (수동 작업 필요)

4. **구 테이블 백업 및 삭제**:
   - `user_platform_credentials` → `_backup`으로 rename
   - 충분한 검증 후 삭제

### Phase 2: Backend API 개발 (2-3일)
1. **SIM 관리 API**:
   - `POST /api/v1/sims` - SIM 추가
   - `GET /api/v1/sims` - SIM 목록
   - `PUT /api/v1/sims/:id` - SIM 수정
   - `DELETE /api/v1/sims/:id` - SIM 삭제

2. **Platform Account API**:
   - `POST /api/v1/platform-accounts` - 계정 추가
   - `GET /api/v1/platform-accounts` - 계정 목록 (SIM별 필터)
   - `PUT /api/v1/platform-accounts/:id` - 계정 수정
   - `DELETE /api/v1/platform-accounts/:id` - 계정 삭제

3. **Job 할당 로직 수정**:
   - `POST /api/v1/jobs` - target_sim_id, target_agent_id 추가
   - `GET /api/v1/jobs/next` - SIM 기반 할당 로직

4. **Quota 체크 로직 수정**:
   - `platform_account_id` 기반으로 체크

### Phase 3: Frontend UI 개발 (3-4일)
1. **SIM 관리 페이지** (NEW):
   - SIM 목록 카드
   - SIM 추가/수정/삭제 폼
   - Agent 연결 상태 표시

2. **플랫폼 관리 페이지** (대폭 수정):
   - 계정별 SIM/Agent 매핑 표시
   - 계정별 할당량 표시
   - 계정 상태 모니터링

3. **Job 생성 페이지** (수정):
   - 할당 방식 선택 UI (모든/SIM/Agent)
   - SIM/Agent 선택 드롭다운

4. **Dashboard 메인** (수정):
   - SIM 통계 표시
   - 계정별 상태 요약

### Phase 4: Android Agent 수정 (1-2일)
1. **등록 화면 수정**:
   - SIM 선택 드롭다운 추가
   - SIM ID를 서버에 전송

2. **Job 처리 로직**:
   - SIM ID 기반 계정 조회
   - 해당 SIM의 credentials 사용

### Phase 5: 테스트 및 검증 (2-3일)
1. **단위 테스트**: 각 API 엔드포인트
2. **통합 테스트**: SIM → Agent → Account → Quota 흐름
3. **E2E 테스트**: Job 생성 → 처리 → 업로드
4. **성능 테스트**: 100개 SIM 시뮬레이션

### Phase 6: 배포 및 롤백 계획 (1일)
1. **스테이징 배포**: 실제 데이터로 테스트
2. **프로덕션 배포**: 점진적 롤아웃
3. **롤백 계획**: DB dump 백업

---

## ⚠️ 주요 고려사항

### 1. 기존 데이터 마이그레이션
- 기존 `user_platform_credentials` 데이터를 `platform_accounts`로 변환
- **문제**: 기존 credential에는 SIM 정보 없음
- **해결**: 관리자가 수동으로 SIM 매핑 필요

### 2. Agent 등록 프로세스 변경
- 기존: Device 정보만 전송
- 신규: Device + SIM ID 전송
- **해결**: Android 앱 업데이트 필요

### 3. OAuth 플로우 수정
- 기존: (user, platform) → credential
- 신규: (user, sim, platform) → account
- **해결**: OAuth callback에서 SIM 선택 UI 추가

### 4. Quota 체크 로직 복잡도 증가
- 기존: (user, platform) 조회
- 신규: (platform_account) → sim → agent 조회
- **해결**: 인덱스 최적화 필요

### 5. Job 할당 로직 복잡도 증가
- 기존: user_id 기반 단순 조회
- 신규: target_sim_id, target_agent_id 고려한 복잡한 로직
- **해결**: DB 쿼리 최적화 및 캐싱

---

## 📊 예상 작업 일정

| Phase | 작업 내용 | 예상 기간 | 우선순위 |
|-------|----------|----------|---------|
| Phase 1 | DB 스키마 마이그레이션 | 1-2일 | 🔴 필수 |
| Phase 2 | Backend API 개발 | 2-3일 | 🔴 필수 |
| Phase 3 | Frontend UI 개발 | 3-4일 | 🔴 필수 |
| Phase 4 | Android Agent 수정 | 1-2일 | 🔴 필수 |
| Phase 5 | 테스트 및 검증 | 2-3일 | 🔴 필수 |
| Phase 6 | 배포 및 롤백 | 1일 | 🔴 필수 |
| **합계** | | **10-15일** | |

---

## ✅ 결론

### 현재 상황
- 현재 구조는 사용자 요구사항을 충족할 수 없음
- SIM 개념이 없어 1:1:1 매핑 불가능
- 할당량이 플랫폼별로만 관리되어 계정별 독립 관리 불가

### 제안 사항
- **SIM 카드 중심 아키텍처로 전면 재설계**
- User → SIM → Agent → PlatformAccount → Quota 구조
- 10-15일 소요 예상

### 다음 단계
1. **승인 대기**: 재설계 방향 확정
2. **우선순위 결정**: 
   - 옵션 A: 즉시 재설계 시작 (권장)
   - 옵션 B: 현재 구조로 Phase 1 완료 후 재설계
3. **작업 시작**: 승인 후 Phase 1 착수

---

**최종 업데이트**: 2026년 3월 4일  
**작성자**: GitHub Copilot  
**검토 필요**: 사용자 승인
