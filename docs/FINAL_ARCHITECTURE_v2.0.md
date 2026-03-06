# 최종 아키텍처 v2.0 - SIM 중심 설계

**확정일**: 2026년 3월 4일  
**승인**: 사용자 승인 완료  
**상태**: 개발 진행

---

## ✅ 확정된 요구사항

### 핵심 구조
```
user_id 1 : sim_id N개 : platform N개 (1:N:N)
sim_id = agent_name (자동 매핑 체계)
```

### 등록 플로우
1. **사용자**: SIM 정보만 등록 (전화번호, 통신사, Google 계정)
2. **시스템**: 나머지 자동 처리
   - Agent 등록 시 SIM 자동 매핑
   - Platform 계정 등록 시 SIM 연결
   - Quota 자동 생성

---

## 📊 최종 데이터 구조

### 1:N:N 관계
```
User (testadmin)
  ↓ 1:N
SIM Card (최대 100개)
  ├─ SIM 1: 010-1111-1111 (SKT)
  │   ├─ Agent 1: "SIM_010-1111-1111" (자동 생성)
  │   └─ Accounts (1:N):
  │       ├─ YouTube Account A → Quota A
  │       ├─ TikTok Account A → Quota A'
  │       └─ Instagram Account A → Quota A''
  │
  ├─ SIM 2: 010-2222-2222 (KT)
  │   ├─ Agent 2: "SIM_010-2222-2222"
  │   └─ Accounts:
  │       ├─ YouTube Account B → Quota B
  │       └─ TikTok Account B → Quota B'
  │
  └─ SIM 3: 010-3333-3333 (LGU+)
      ├─ Agent 3: "SIM_010-3333-3333"
      └─ Accounts:
          └─ YouTube Account C → Quota C
```

---

## 🗄️ DB 스키마

### **sim_cards** (핵심 테이블)
```sql
CREATE TABLE sim_cards (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- SIM 정보 (필수)
  sim_number VARCHAR(20) UNIQUE NOT NULL,  -- 010-1234-5678
  carrier VARCHAR(50),                     -- SKT, KT, LGU+
  
  -- Google 계정 (1 SIM = 1 Google Account)
  google_email VARCHAR(100) UNIQUE,
  google_account_status VARCHAR(20) DEFAULT 'active',  -- active, banned, suspended
  
  -- 메타데이터
  nickname VARCHAR(100),                   -- 별칭 (선택)
  notes TEXT,
  status VARCHAR(20) DEFAULT 'active',
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_sim_user (user_id),
  INDEX idx_sim_number (sim_number)
);
```

### **agents** (SIM과 1:1 매핑)
```sql
CREATE TABLE agents (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_id INTEGER UNIQUE NOT NULL REFERENCES sim_cards(id) ON DELETE CASCADE,  -- 1:1 필수!
  
  -- 기기 정보
  device_name VARCHAR(100) NOT NULL,       -- 자동 생성: "SIM_010-1111-1111"
  device_id VARCHAR(100) UNIQUE NOT NULL,
  device_model VARCHAR(50),
  
  -- 연결 정보
  api_key VARCHAR(128) UNIQUE NOT NULL,
  status VARCHAR(20) DEFAULT 'offline',
  last_heartbeat TIMESTAMPTZ,
  ip_address INET,
  
  -- Android 정보
  android_version VARCHAR(20),
  apk_version VARCHAR(20),
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_agent_sim (sim_id),
  CONSTRAINT uq_agent_sim UNIQUE (sim_id)  -- 1:1 강제
);
```

### **platform_accounts** (SIM당 여러 플랫폼 계정)
```sql
CREATE TABLE platform_accounts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_id INTEGER NOT NULL REFERENCES sim_cards(id) ON DELETE CASCADE,
  platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
  
  -- 계정 정보
  account_name VARCHAR(100),               -- "게임채널 A"
  account_identifier VARCHAR(100),         -- 채널 ID
  
  -- 인증 정보 (암호화)
  credentials JSONB NOT NULL,
  
  -- 상태
  status VARCHAR(20) DEFAULT 'active',
  last_validated TIMESTAMPTZ,
  last_used TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_account_sim (sim_id),
  INDEX idx_account_platform (platform_id),
  UNIQUE (sim_id, platform_id, account_name)  -- SIM당 플랫폼별 계정 이름 중복 불가
);
```

### **upload_quotas** (계정별 할당량)
```sql
CREATE TABLE upload_quotas (
  id SERIAL PRIMARY KEY,
  platform_account_id INTEGER UNIQUE NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
  
  daily_limit INTEGER DEFAULT 0,
  weekly_limit INTEGER DEFAULT 0,
  monthly_limit INTEGER DEFAULT 0,
  
  used_today INTEGER DEFAULT 0,
  used_week INTEGER DEFAULT 0,
  used_month INTEGER DEFAULT 0,
  
  last_daily_reset TIMESTAMPTZ DEFAULT NOW(),
  last_weekly_reset TIMESTAMPTZ DEFAULT NOW(),
  last_monthly_reset TIMESTAMPTZ DEFAULT NOW(),
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT uq_quota_account UNIQUE (platform_account_id)
);
```

### **jobs** (SIM/Agent 타겟팅)
```sql
CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  
  -- 할당 타겟
  target_sim_id INTEGER REFERENCES sim_cards(id),      -- 특정 SIM 지정
  target_agent_id INTEGER REFERENCES agents(id),       -- 특정 Agent 지정
  assigned_agent_id INTEGER REFERENCES agents(id),     -- 실제 처리 Agent
  
  target_platform_id INTEGER NOT NULL REFERENCES platforms(id),
  
  -- Job 정보
  title TEXT,
  script TEXT,
  status VARCHAR(20) DEFAULT 'pending',
  priority INTEGER DEFAULT 5,
  
  video_path TEXT,
  video_url TEXT,
  error_message TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  assigned_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  
  INDEX idx_job_sim (target_sim_id),
  INDEX idx_job_status (status),
  INDEX idx_job_priority (priority)
);
```

---

## 🔄 사용 시나리오

### 1. SIM 등록 (사용자)
```
Dashboard → "SIM 관리" → "SIM 추가"

입력:
  - 전화번호: 010-1234-5678 (필수)
  - 통신사: SKT (선택)
  - Google 계정: game.channel.a@gmail.com (선택)
  - 별칭: "게임채널용 SIM" (선택)

→ sim_cards INSERT
  sim_id=5, sim_number="010-1234-5678", user_id=1
```

### 2. Agent 등록 (Android 앱)
```
Android 앱 실행 → "등록" 화면

시스템이 자동으로:
  1. 기기의 SIM 번호 읽기: 010-1234-5678
  2. Backend에서 sim_id 조회: sim_id=5
  3. device_name 자동 생성: "SIM_010-1234-5678"
  4. agents INSERT:
       sim_id=5,
       device_name="SIM_010-1234-5678",
       device_id="랜덤UUID",
       api_key="자동생성"

사용자는 아무것도 입력 안함!
```

### 3. YouTube 계정 등록 (Dashboard)
```
Dashboard → "플랫폼 관리" → YouTube 카드

SIM 선택: 010-1234-5678 (sim_id=5)
계정 이름: "게임채널 A"
OAuth 시작 → Google 로그인

→ platform_accounts INSERT
  sim_id=5, platform_id=1 (YouTube), account_name="게임채널 A"

→ upload_quotas 자동 생성
  platform_account_id=20, daily_limit=10 (기본값)
```

### 4. Job 생성 (통합)
```
Dashboard → "Job 생성"

할당 방식:
  ◉ 모든 Agent (target_sim_id=NULL, target_agent_id=NULL)
  ○ 특정 SIM: 010-1234-5678
  ○ 특정 Agent: SIM_010-1234-5678

플랫폼: YouTube
제목: "게임 공략 영상"

→ jobs INSERT
  user_id=1,
  target_sim_id=NULL (모든 Agent가 처리 가능),
  target_platform_id=1
```

### 5. Job 할당 (Backend)
```
Agent가 /api/v1/jobs/next 호출
  agent_id=10, sim_id=5

Backend 로직:
  SELECT * FROM jobs
  WHERE user_id = 1
    AND status = 'pending'
    AND (
      target_agent_id = 10           -- 이 Agent 지정
      OR target_sim_id = 5           -- 이 SIM 지정
      OR (target_agent_id IS NULL AND target_sim_id IS NULL)  -- 모든 Agent
    )
  ORDER BY priority DESC, created_at ASC
  LIMIT 1;

→ Job 반환 (job_id=100)
```

### 6. 영상 업로드
```
Agent가 영상 생성 완료 → 플랫폼 계정 조회

Backend:
  1. agents 에서 sim_id=5 확인
  2. platform_accounts 에서 sim_id=5 AND platform_id=1 조회
  3. YouTube 계정 "게임채널 A" credentials 사용
  4. 업로드 성공
  5. upload_quotas 에서 used_today++
```

---

## 🎨 UI 구조

### Dashboard → SIM 관리 (NEW!)
```
┌───────────────────────────────────────────────────┐
│ 📱 SIM 카드 관리 (3개 등록 중)                    │
├───────────────────────────────────────────────────┤
│ [+ SIM 추가]  [📊 통계]  [🔄 새로고침]            │
│                                                    │
│ ┌─────────────────────────────────────────────┐  │
│ │ 🟢 SIM 1: 010-1111-1111 (SKT)              │  │
│ │ Google: game.channel.a@gmail.com           │  │
│ │ Agent: SIM_010-1111-1111 (Galaxy S21) 🟢   │  │
│ │ 계정: YouTube 1, TikTok 1, Instagram 1     │  │
│ │ [상세보기] [수정]                           │  │
│ └─────────────────────────────────────────────┘  │
│                                                    │
│ ┌─────────────────────────────────────────────┐  │
│ │ ⚠️  SIM 2: 010-2222-2222 (KT) - Agent 미연결│  │
│ │ Google: music.channel.b@gmail.com          │  │
│ │ Agent: 미등록 (Android 앱 등록 필요)       │  │
│ │ 계정: YouTube 1, TikTok 1                  │  │
│ │ [Agent 등록 가이드]                        │  │
│ └─────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

### Dashboard → 플랫폼 관리
```
┌───────────────────────────────────────────────────┐
│ 📺 YouTube (3개 SIM, 3개 계정)                    │
├───────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐  │
│ │ 계정 1: 게임채널 A                          │  │
│ │ 📱 SIM: 010-1111-1111                      │  │
│ │ 🤖 Agent: SIM_010-1111-1111 🟢 Online      │  │
│ │ 📊 할당량: 일일 3/10, 주간 15/50           │  │
│ │ ✅ 정상                                     │  │
│ └─────────────────────────────────────────────┘  │
│                                                    │
│ [+ 계정 추가 (OAuth)]                              │
└───────────────────────────────────────────────────┘
```

---

## 🔧 개발 단계

### Phase 1: DB 마이그레이션 (현재 진행 중)
- [x] sim_cards 테이블 생성
- [x] agents 테이블 수정 (sim_id 추가)
- [x] platform_accounts 테이블 생성
- [x] upload_quotas 수정
- [x] jobs 수정
- [ ] 마이그레이션 스크립트 작성
- [ ] 테스트 데이터 생성

### Phase 2: Backend API
- [ ] SIM CRUD API
- [ ] Agent 자동 등록 로직
- [ ] Platform Account CRUD
- [ ] Job 할당 로직 (SIM 기반)
- [ ] Quota 체크 (계정 기반)

### Phase 3: Frontend UI
- [ ] SIM 관리 페이지
- [ ] 플랫폼 관리 (SIM별 표시)
- [ ] Job 생성 (SIM/Agent 선택)

### Phase 4: Android Agent
- [ ] SIM 번호 자동 읽기
- [ ] 자동 등록 (device_name 생성)

---

## ✅ 핵심 원칙

1. **SIM이 중심**: 모든 데이터는 SIM을 기준으로 관리
2. **자동화**: 사용자는 SIM 정보만 등록, 나머지는 시스템이 처리
3. **1:1 매핑**: SIM과 Agent는 1:1 (sim_id = agent_name)
4. **1:N:N**: User → SIM (1:N) → Platform (N:N)
5. **독립적 할당량**: 계정별로 독립적인 quota

---

**다음 단계**: Phase 1 DB 마이그레이션 스크립트 작성 시작
