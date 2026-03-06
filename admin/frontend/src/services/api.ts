export type HealthResponse = {
  status: string
  database: string
  redis: string
  services: {
    api: string
  }
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

export type MeResponse = {
  id: number
  username: string
  email: string
  role: string
  created_at: string
}

export type RegisterRequest = {
  username: string
  email: string
  password: string
}

export type AgentStatsResponse = {
  total: number
  by_status: Record<string, number>
  online_count: number
  offline_count: number
}

export type JobStatsResponse = {
  total: number
  by_status: Record<string, number>
  pending_count: number
  processing_count: number
  completed_count: number
  failed_count: number
  avg_processing_time: number | null
}

export type AgentItem = {
  id: number
  device_name: string
  status: string
  last_heartbeat: string | null
  disk_usage_percent?: number
}

export type JobItem = {
  id: number
  title: string
  status: string
  priority: number
  created_at: string
}

export type PublishYoutubeRequest = {
  credential_id?: number
  title?: string
  description?: string
  tags?: string[]
  privacy_status?: 'private' | 'public' | 'unlisted'
}

export type PublishTiktokRequest = {
  credential_id?: number
  caption?: string
  headless?: boolean
}

export type UploadQuotaItem = {
  id: number
  user_id: number
  platform_id: number
  daily_limit: number
  weekly_limit: number
  monthly_limit: number
  used_today: number
  used_week: number
  used_month: number
  remaining_daily: number
  remaining_weekly: number
  remaining_monthly: number
  is_quota_exceeded: boolean
  created_at: string
  updated_at: string
}

export type UploadQuotaCreateRequest = {
  platform_id: number
  daily_limit: number
  weekly_limit: number
  monthly_limit: number
}

export type UploadQuotaUpdateRequest = {
  daily_limit?: number
  weekly_limit?: number
  monthly_limit?: number
}

export type PlatformItem = {
  id: number
  platform_code: string
  platform_name: string
  is_active?: boolean
  auth_type?: string
  api_endpoint?: string | null
  documentation_url?: string | null
  required_fields?: Record<string, unknown> | null
  // 플랫폼별 제한 설정 (확장 가능)
  constraints?: {
    hourly_limit?: number
    daily_limit?: number
    monthly_limit?: number
    max_video_size_mb?: number
    max_duration_seconds?: number
    supported_resolutions?: string[]
    supported_formats?: string[]
  }
}

export type CredentialItem = {
  id: number
  user_id: number
  platform_id: number
  credential_name: string | null
  is_default: boolean
  status: string
  last_validated: string | null
  created_at: string
  updated_at: string
  has_access_token: boolean
  has_refresh_token: boolean
}

export type CredentialCreateRequest = {
  platform_id: number
  credential_name?: string
  credentials: Record<string, unknown>
  is_default?: boolean
}

export type OAuthAuthorizeResponse = {
  authorization_url: string
  state: string
}

export type TrendItem = {
  id: number
  source: string
  keyword: string
  topic: string | null
  category: string | null
  trend_score: number
  view_count: number
  video_count: number
  growth_rate: number
  language: string
  region: string
  collected_at: string
  created_at: string
}

export type TrendSourceItem = {
  code: string
  label: string
  icon: string
  description: string
  enabled: boolean
  supports_collection: boolean
}

export type ScriptItem = {
  id: number
  user_id: number
  trend_id: number | null
  title: string
  content: string
  hook: string | null
  body: string | null
  cta: string | null
  ai_model: string | null
  quality_score: number
  viral_potential: number
  used_count: number
  is_approved: boolean
  is_archived: boolean
  language: string
  created_at: string
  updated_at: string
}

export type ScriptGenerateRequest = {
  topic: string
  trend_id?: number
  target_audience?: string
  platform?: string
  language?: string
  duration?: number
}

export type JobCreateRequest = {
  platform_id: number
  title: string
  script: string
  source_language: string
  target_languages: string[]
  priority: number
}

const API_BASE_URL = 'http://localhost:8001'

export async function login(username: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams()
  body.set('username', username)
  body.set('password', password)

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  })

  if (!response.ok) {
    throw new Error('아이디 또는 비밀번호가 올바르지 않습니다.')
  }

  return response.json() as Promise<LoginResponse>
}

export async function register(payload: RegisterRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = '회원가입에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = '회원가입에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function fetchMe(token: string): Promise<MeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('세션이 만료되었습니다. 다시 로그인해주세요.')
  }

  return response.json() as Promise<MeResponse>
}

export async function fetchAgentStats(token: string): Promise<AgentStatsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agents/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Agent 통계 조회에 실패했습니다.')
  }

  return response.json() as Promise<AgentStatsResponse>
}

export async function fetchJobStats(token: string): Promise<JobStatsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Job 통계 조회에 실패했습니다.')
  }

  return response.json() as Promise<JobStatsResponse>
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`Health API request failed: ${response.status}`)
  }
  return response.json() as Promise<HealthResponse>
}

export async function fetchAgents(token: string): Promise<AgentItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agents?limit=5`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Agent 목록 조회에 실패했습니다.')
  }

  return response.json() as Promise<AgentItem[]>
}

export async function fetchJobs(token: string): Promise<JobItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs?limit=5`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Job 목록 조회에 실패했습니다.')
  }

  return response.json() as Promise<JobItem[]>
}

export async function fetchPlatforms(): Promise<PlatformItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platforms`)

  if (!response.ok) {
    throw new Error('플랫폼 목록 조회에 실패했습니다.')
  }

  return response.json() as Promise<PlatformItem[]>
}

export async function createPlatform(token: string, data: {
  platform_code: string
  platform_name: string
  auth_type: string
  api_endpoint?: string
  documentation_url?: string
  required_fields?: Record<string, unknown>
  constraints?: {
    hourly_limit?: number
    daily_limit?: number
    monthly_limit?: number
    max_video_size_mb?: number
    max_duration_seconds?: number
    supported_resolutions?: string[]
    supported_formats?: string[]
  }
}): Promise<PlatformItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platforms`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '플랫폼 생성에 실패했습니다.' }))
    throw new Error(errorData.detail || '플랫폼 생성에 실패했습니다.')
  }

  return response.json() as Promise<PlatformItem>
}

export async function updatePlatform(token: string, platformId: number, data: {
  platform_name?: string
  auth_type?: string
  api_endpoint?: string
  documentation_url?: string
  required_fields?: Record<string, unknown>
  is_active?: boolean
  constraints?: {
    hourly_limit?: number
    daily_limit?: number
    monthly_limit?: number
    max_video_size_mb?: number
    max_duration_seconds?: number
    supported_resolutions?: string[]
    supported_formats?: string[]
  }
}): Promise<PlatformItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platforms/${platformId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '플랫폼 수정에 실패했습니다.' }))
    throw new Error(errorData.detail || '플랫폼 수정에 실패했습니다.')
  }

  return response.json() as Promise<PlatformItem>
}

export async function deletePlatform(token: string, platformId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platforms/${platformId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '플랫폼 삭제에 실패했습니다.' }))
    throw new Error(errorData.detail || '플랫폼 삭제에 실패했습니다.')
  }
}

export async function fetchCredentials(token: string): Promise<CredentialItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/credentials`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Credential 목록 조회에 실패했습니다.')
  }

  return response.json() as Promise<CredentialItem[]>
}

export async function createCredential(token: string, payload: CredentialCreateRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/credentials`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = 'Credential 생성에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'Credential 생성에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function startYoutubeOAuth(token: string, platformId: number, redirectUri: string): Promise<OAuthAuthorizeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/credentials/oauth/youtube/authorize`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      platform_id: platformId,
      redirect_uri: redirectUri,
    }),
  })

  if (!response.ok) {
    let message = 'YouTube OAuth 시작에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'YouTube OAuth 시작에 실패했습니다.'
    }
    throw new Error(message)
  }

  return response.json() as Promise<OAuthAuthorizeResponse>
}

export async function completeYoutubeOAuth(code: string, state: string, platformId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/credentials/oauth/youtube/callback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code,
      state,
      platform_id: platformId,
    }),
  })

  if (!response.ok) {
    let message = 'YouTube OAuth 콜백 처리에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'YouTube OAuth 콜백 처리에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function fetchTrends(token: string): Promise<TrendItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/trends?limit=30`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('트렌드 조회에 실패했습니다.')
  }

  return response.json() as Promise<TrendItem[]>
}

export async function fetchTrendSources(token: string): Promise<TrendSourceItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/trends/sources`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('트렌드 소스 조회에 실패했습니다.')
  }

  return response.json() as Promise<TrendSourceItem[]>
}

export async function collectTrends(token: string, regionCode: string, sources: string[]): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/trends/collect`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ region_code: regionCode, sources }),
  })

  if (!response.ok) {
    let message = '트렌드 수집에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = '트렌드 수집에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function fetchScripts(token: string): Promise<ScriptItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/scripts?limit=10`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('스크립트 목록 조회에 실패했습니다.')
  }

  return response.json() as Promise<ScriptItem[]>
}

export async function generateScript(token: string, payload: ScriptGenerateRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/scripts`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = '스크립트 생성에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = '스크립트 생성에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function createJob(token: string, payload: JobCreateRequest): Promise<JobItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = 'Job 생성에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'Job 생성에 실패했습니다.'
    }
    throw new Error(message)
  }

  return response.json() as Promise<JobItem>
}

export async function cancelJob(token: string, jobId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/cancel`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let message = 'Job 취소에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'Job 취소에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function retryJob(token: string, jobId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/retry`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let message = 'Job 재시도에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'Job 재시도에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function publishJobToYoutube(token: string, jobId: number, payload?: PublishYoutubeRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/publish/youtube`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload ?? {}),
  })

  if (!response.ok) {
    let message = 'YouTube 게시에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'YouTube 게시에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function publishJobToTiktok(token: string, jobId: number, payload?: PublishTiktokRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/publish/tiktok`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload ?? {}),
  })

  if (!response.ok) {
    let message = 'TikTok 게시에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'TikTok 게시에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function fetchUploadQuotas(token: string): Promise<UploadQuotaItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload-quotas`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('업로드 할당량 조회에 실패했습니다.')
  }

  return response.json() as Promise<UploadQuotaItem[]>
}

export async function createUploadQuota(token: string, payload: UploadQuotaCreateRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload-quotas`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = '업로드 할당량 생성에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = '업로드 할당량 생성에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function updateUploadQuota(token: string, quotaId: number, payload: UploadQuotaUpdateRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload-quotas/${quotaId}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let message = '업로드 할당량 수정에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = '업로드 할당량 수정에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function deleteUploadQuota(token: string, quotaId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload-quotas/${quotaId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let message = '업로드 할당량 삭제에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = '업로드 할당량 삭제에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function resetDailyQuotas(token: string): Promise<{ reset_count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload-quotas/reset/daily`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('일일 할당량 초기화에 실패했습니다.')
  }

  return response.json() as Promise<{ reset_count: number }>
}

export async function resetWeeklyQuotas(token: string): Promise<{ reset_count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload-quotas/reset/weekly`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('주간 할당량 초기화에 실패했습니다.')
  }

  return response.json() as Promise<{ reset_count: number }>
}

export async function resetMonthlyQuotas(token: string): Promise<{ reset_count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload-quotas/reset/monthly`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('월간 할당량 초기화에 실패했습니다.')
  }

  return response.json() as Promise<{ reset_count: number }>
}

export async function recordAgentDiskCleanup(token: string, agentId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agents/${agentId}/disk-cleanup`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let message = 'Agent 디스크 정리 기록에 실패했습니다.'
    try {
      const data = (await response.json()) as { detail?: string; error?: string }
      message = data.detail ?? data.error ?? message
    } catch {
      message = 'Agent 디스크 정리 기록에 실패했습니다.'
    }
    throw new Error(message)
  }
}

// ==================== SIM Card API (v2.0 Architecture) ====================

export type SimCardItem = {
  id: number
  user_id: number
  sim_number: string
  carrier: string | null
  google_email: string | null
  google_account_status: string
  nickname: string | null
  notes: string | null
  status: string
  created_at: string
  updated_at: string
  display_name: string
  agent_status: string
  total_accounts: number
  platform_accounts: Array<{
    id: number
    platform_id: number
    platform_name: string | null
    account_name: string
    account_identifier: string | null
    status: string
    is_primary: boolean
    last_validated: string | null
    created_at: string | null
  }>
}

export type SimCardDetailItem = SimCardItem & {
  agent: {
    id: number
    device_name: string
    device_id: string
    status: string
    last_heartbeat: string | null
    android_version: string | null
    apk_version: string | null
  } | null
  platform_accounts: Array<{
    id: number
    platform_id: number
    account_name: string
    status: string
    is_primary: boolean
  }>
}

export type SimCardCreateRequest = {
  sim_number: string
  carrier?: string
  google_email?: string
  nickname?: string
  notes?: string
}

export type SimCardUpdateRequest = {
  carrier?: string
  google_email?: string
  google_account_status?: 'active' | 'banned' | 'suspended'
  nickname?: string
  notes?: string
  status?: 'active' | 'inactive' | 'banned'
}

export async function fetchSimCards(token: string, filters?: {
  status_filter?: string
  carrier_filter?: string
}): Promise<SimCardItem[]> {
  const params = new URLSearchParams()
  if (filters?.status_filter) params.append('status_filter', filters.status_filter)
  if (filters?.carrier_filter) params.append('carrier_filter', filters.carrier_filter)

  const url = `${API_BASE_URL}/api/v1/sims${params.toString() ? '?' + params.toString() : ''}`
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('SIM 카드 목록 조회에 실패했습니다.')
  }

  return response.json() as Promise<SimCardItem[]>
}

export async function fetchSimCardDetail(token: string, simId: number): Promise<SimCardDetailItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sims/${simId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('SIM 카드 상세 조회에 실패했습니다.')
  }

  return response.json() as Promise<SimCardDetailItem>
}

export async function createSimCard(token: string, data: SimCardCreateRequest): Promise<SimCardItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sims`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    let message = 'SIM 카드 등록에 실패했습니다.'
    try {
      const errData = (await response.json()) as { detail?: string; error?: string }
      message = errData.detail ?? errData.error ?? message
    } catch {
      message = 'SIM 카드 등록에 실패했습니다.'
    }
    throw new Error(message)
  }

  return response.json() as Promise<SimCardItem>
}

export async function updateSimCard(token: string, simId: number, data: SimCardUpdateRequest): Promise<SimCardItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sims/${simId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    let message = 'SIM 카드 수정에 실패했습니다.'
    try {
      const errData = (await response.json()) as { detail?: string; error?: string }
      message = errData.detail ?? errData.error ?? message
    } catch {
      message = 'SIM 카드 수정에 실패했습니다.'
    }
    throw new Error(message)
  }

  return response.json() as Promise<SimCardItem>
}

export async function deleteSimCard(token: string, simId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sims/${simId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let message = 'SIM 카드 삭제에 실패했습니다.'
    try {
      const errData = (await response.json()) as { detail?: string; error?: string }
      message = errData.detail ?? errData.error ?? message
    } catch {
      message = 'SIM 카드 삭제에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function fetchSimCardStats(token: string, simId: number): Promise<{
  sim_id: number
  sim_number: string
  display_name: string
  status: string
  agent_status: string
  total_platform_accounts: number
  total_jobs: number
  completed_jobs: number
  success_rate: number
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sims/${simId}/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('SIM 카드 통계 조회에 실패했습니다.')
  }

  return response.json()
}

// ==================== Platform Account API (v2.0 Architecture) ====================

export type PlatformAccountItem = {
  id: number
  user_id: number
  sim_id: number
  platform_id: number
  account_name: string
  account_identifier: string | null
  status: string
  last_validated: string | null
  last_used: string | null
  ban_detected_at: string | null
  ban_reason: string | null
  is_primary: boolean
  notes: string | null
  created_at: string
  updated_at: string
  display_name: string
  is_active: boolean
  is_banned: boolean
  has_quota: boolean
}

export type PlatformAccountDetailItem = PlatformAccountItem & {
  sim_info: {
    id: number
    sim_number: string
    carrier: string | null
    status: string
  } | null
  platform_info: {
    id: number
    platform_code: string
    platform_name: string
  } | null
  stats: {
    total_uploads: number
    successful_uploads: number
    failed_uploads: number
    success_rate: number
    consecutive_failures: number
    last_upload_at: string | null
  } | null
  quota: {
    id: number
    daily_limit: number
    weekly_limit: number
    monthly_limit: number
    used_today: number
    used_week: number
    used_month: number
    remaining_daily: number
    remaining_weekly: number
    remaining_monthly: number
    is_exceeded: boolean
  } | null
}

export type PlatformAccountCreateRequest = {
  sim_id: number
  platform_id: number
  account_name: string
  account_identifier?: string
  credentials: Record<string, unknown>
  is_primary?: boolean
  notes?: string
}

export type PlatformAccountUpdateRequest = {
  account_name?: string
  account_identifier?: string
  credentials?: Record<string, unknown>
  status?: 'active' | 'banned' | 'expired' | 'inactive'
  is_primary?: boolean
  notes?: string
}

export async function fetchPlatformAccounts(token: string, filters?: {
  sim_id?: number
  platform_id?: number
  status_filter?: string
}): Promise<PlatformAccountItem[]> {
  const params = new URLSearchParams()
  if (filters?.sim_id) params.append('sim_id', String(filters.sim_id))
  if (filters?.platform_id) params.append('platform_id', String(filters.platform_id))
  if (filters?.status_filter) params.append('status_filter', filters.status_filter)

  const url = `${API_BASE_URL}/api/v1/platform-accounts${params.toString() ? '?' + params.toString() : ''}`
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('플랫폼 계정 목록 조회에 실패했습니다.')
  }

  return response.json() as Promise<PlatformAccountItem[]>
}

export async function fetchPlatformAccountDetail(token: string, accountId: number): Promise<PlatformAccountDetailItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platform-accounts/${accountId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('플랫폼 계정 상세 조회에 실패했습니다.')
  }

  return response.json() as Promise<PlatformAccountDetailItem>
}

export async function createPlatformAccount(token: string, data: PlatformAccountCreateRequest): Promise<PlatformAccountItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platform-accounts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    let message = '플랫폼 계정 등록에 실패했습니다.'
    try {
      const errData = (await response.json()) as { detail?: string; error?: string }
      message = errData.detail ?? errData.error ?? message
    } catch {
      message = '플랫폼 계정 등록에 실패했습니다.'
    }
    throw new Error(message)
  }

  return response.json() as Promise<PlatformAccountItem>
}

export async function updatePlatformAccount(token: string, accountId: number, data: PlatformAccountUpdateRequest): Promise<PlatformAccountItem> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platform-accounts/${accountId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    let message = '플랫폼 계정 수정에 실패했습니다.'
    try {
      const errData = (await response.json()) as { detail?: string; error?: string }
      message = errData.detail ?? errData.error ?? message
    } catch {
      message = '플랫폼 계정 수정에 실패했습니다.'
    }
    throw new Error(message)
  }

  return response.json() as Promise<PlatformAccountItem>
}

export async function deletePlatformAccount(token: string, accountId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platform-accounts/${accountId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let message = '플랫폼 계정 삭제에 실패했습니다.'
    try {
      const errData = (await response.json()) as { detail?: string; error?: string }
      message = errData.detail ?? errData.error ?? message
    } catch {
      message = '플랫폼 계정 삭제에 실패했습니다.'
    }
    throw new Error(message)
  }
}

export async function validatePlatformCredentials(
  token: string,
  platformId: number,
  credentials: Record<string, unknown>
): Promise<{
  valid: boolean
  platform_code: string
  platform_name: string
  errors: string[]
  warnings: string[]
  message: string
  checked_fields: string[]
  missing_fields: string[]
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platform-accounts/validate-credentials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      platform_id: platformId,
      credentials,
    }),
  })

  if (!response.ok) {
    let message = '인증 정보 검증에 실패했습니다.'
    try {
      const errData = (await response.json()) as { detail?: string; error?: string }
      message = errData.detail ?? errData.error ?? message
    } catch {
      message = '인증 정보 검증에 실패했습니다.'
    }
    throw new Error(message)
  }

  return response.json()
}

export async function banPlatformAccount(token: string, accountId: number, reason: string): Promise<{ message: string; reason: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platform-accounts/${accountId}/ban`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reason }),
  })

  if (!response.ok) {
    throw new Error('플랫폼 계정 차단에 실패했습니다.')
  }

  return response.json()
}

export async function activatePlatformAccount(token: string, accountId: number): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/platform-accounts/${accountId}/activate`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('플랫폼 계정 활성화에 실패했습니다.')
  }

  return response.json()
}

