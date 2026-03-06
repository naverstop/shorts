import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  cancelJob,
  collectTrends,
  completeYoutubeOAuth,
  createCredential,
  createUploadQuota,
  createJob,
  deleteUploadQuota,
  fetchAgents,
  fetchAgentStats,
  fetchCredentials,
  fetchHealth,
  fetchJobs,
  fetchJobStats,
  fetchPlatforms,
  fetchUploadQuotas,
  publishJobToYoutube,
  publishJobToTiktok,
  fetchScripts,
  fetchTrends,
  generateScript,
  recordAgentDiskCleanup,
  resetDailyQuotas,
  resetWeeklyQuotas,
  resetMonthlyQuotas,
  retryJob,
  startYoutubeOAuth,
  type AgentItem,
  type AgentStatsResponse,
  type CredentialItem,
  type HealthResponse,
  type JobItem,
  type JobStatsResponse,
  type PlatformItem,
  type UploadQuotaItem,
  type ScriptItem,
  type TrendItem,
  updateUploadQuota,
} from '../services/api'

type DashboardPageProps = {
  username: string
  token: string
  onLogout: () => void
}

type DashboardWsMessage = {
  type: string
  agent_id?: number
  job_id?: number
  status?: string
  data?: Record<string, unknown>
  timestamp?: string
}

function DashboardPage({ username, token, onLogout }: DashboardPageProps) {
  const navigate = useNavigate()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [agentStats, setAgentStats] = useState<AgentStatsResponse | null>(null)
  const [jobStats, setJobStats] = useState<JobStatsResponse | null>(null)
  const [agents, setAgents] = useState<AgentItem[]>([])
  const [jobs, setJobs] = useState<JobItem[]>([])
  const [platforms, setPlatforms] = useState<PlatformItem[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [jobTitle, setJobTitle] = useState('')
  const [jobScript, setJobScript] = useState('')
  const [selectedPlatformId, setSelectedPlatformId] = useState<number | null>(null)
  const [jobSubmitError, setJobSubmitError] = useState<string | null>(null)
  const [jobSubmitting, setJobSubmitting] = useState(false)
  const [jobActionError, setJobActionError] = useState<string | null>(null)
  const [jobActionLoadingId, setJobActionLoadingId] = useState<number | null>(null)
  const [jobPublishMessage, setJobPublishMessage] = useState<string | null>(null)
  const [agentActionError, setAgentActionError] = useState<string | null>(null)
  const [agentActionLoadingId, setAgentActionLoadingId] = useState<number | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [lastRealtimeEvent, setLastRealtimeEvent] = useState<string | null>(null)
  const [credentials, setCredentials] = useState<CredentialItem[]>([])
  const [trends, setTrends] = useState<TrendItem[]>([])
  const [scripts, setScripts] = useState<ScriptItem[]>([])
  const [credentialName, setCredentialName] = useState('')
  const [credentialJson, setCredentialJson] = useState('{"api_key":""}')
  const [credentialPlatformId, setCredentialPlatformId] = useState<number | null>(null)
  const [credentialMessage, setCredentialMessage] = useState<string | null>(null)
  const [credentialLoading, setCredentialLoading] = useState(false)
  const [oauthCode, setOauthCode] = useState('')
  const [oauthState, setOauthState] = useState('')
  const [oauthMessage, setOauthMessage] = useState<string | null>(null)
  const [trendRegion, setTrendRegion] = useState('KR')
  const [trendLoading, setTrendLoading] = useState(false)
  const [trendMessage, setTrendMessage] = useState<string | null>(null)
  const [scriptTopic, setScriptTopic] = useState('')
  const [scriptTrendId, setScriptTrendId] = useState<string>('')
  const [scriptLoading, setScriptLoading] = useState(false)
  const [scriptMessage, setScriptMessage] = useState<string | null>(null)
  const [quotas, setQuotas] = useState<UploadQuotaItem[]>([])
  const [quotaMessage, setQuotaMessage] = useState<string | null>(null)
  const [quotaPlatformId, setQuotaPlatformId] = useState<number | null>(null)
  const [quotaDaily, setQuotaDaily] = useState('10')
  const [quotaWeekly, setQuotaWeekly] = useState('50')
  const [quotaMonthly, setQuotaMonthly] = useState('200')

  const loadDashboard = async () => {
    setLoading(true)
    setErrorMessage(null)
    try {
      const [healthData, agentStatsData, jobStatsData, agentList, jobList, platformList, credentialList, trendList, scriptList, quotaList] = await Promise.all([
        fetchHealth(),
        fetchAgentStats(token),
        fetchJobStats(token),
        fetchAgents(token),
        fetchJobs(token),
        fetchPlatforms(),
        fetchCredentials(token),
        fetchTrends(token),
        fetchScripts(token),
        fetchUploadQuotas(token),
      ])
      setHealth(healthData)
      setAgentStats(agentStatsData)
      setJobStats(jobStatsData)
      setAgents(agentList)
      setJobs(jobList)
      setPlatforms(platformList)
      setCredentials(credentialList)
      setTrends(trendList)
      setScripts(scriptList)
      setQuotas(quotaList)
      if (!selectedPlatformId && platformList.length > 0) {
        setSelectedPlatformId(platformList[0].id)
      }
      if (!credentialPlatformId && platformList.length > 0) {
        setCredentialPlatformId(platformList[0].id)
      }
      if (!quotaPlatformId && platformList.length > 0) {
        setQuotaPlatformId(platformList[0].id)
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDashboard()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  useEffect(() => {
    const wsUrl = 'ws://localhost:8001/ws/dashboard'
    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      setWsConnected(true)
      websocket.send('ping')
    }

    websocket.onclose = () => {
      setWsConnected(false)
    }

    websocket.onerror = () => {
      setWsConnected(false)
    }

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as DashboardWsMessage

        if (message.type === 'agent_update' && message.agent_id) {
          const nextStatus = String(message.data?.status ?? '')
          setAgents((prev) =>
            prev.map((agent) =>
              agent.id === message.agent_id
                ? {
                    ...agent,
                    status: nextStatus || agent.status,
                  }
                : agent,
            ),
          )
          setLastRealtimeEvent(`Agent #${message.agent_id} 상태 업데이트`)
          return
        }

        if (message.type === 'agent_status' && message.agent_id) {
          const nextStatus = String(message.status ?? '')
          setAgents((prev) =>
            prev.map((agent) =>
              agent.id === message.agent_id
                ? {
                    ...agent,
                    status: nextStatus || agent.status,
                  }
                : agent,
            ),
          )
          setLastRealtimeEvent(`Agent #${message.agent_id} ${nextStatus}`)
          return
        }

        if (message.type === 'job_update' && message.job_id) {
          const nextStatus = String(message.data?.new_status ?? message.data?.status ?? '')
          setJobs((prev) =>
            prev.map((job) =>
              job.id === message.job_id
                ? {
                    ...job,
                    status: nextStatus || job.status,
                  }
                : job,
            ),
          )
          setLastRealtimeEvent(`Job #${message.job_id} 상태 업데이트`)
        }
      } catch {
        // ignore non-json ping/pong messages
      }
    }

    return () => {
      websocket.close()
    }
  }, [token])

  const handleCreateJob = async (event: FormEvent) => {
    event.preventDefault()
    setJobSubmitError(null)

    if (!selectedPlatformId || !jobTitle.trim() || !jobScript.trim()) {
      setJobSubmitError('플랫폼, 제목, 스크립트를 모두 입력해주세요.')
      return
    }

    setJobSubmitting(true)
    try {
      await createJob(token, {
        platform_id: selectedPlatformId,
        title: jobTitle.trim(),
        script: jobScript.trim(),
        source_language: 'ko',
        target_languages: ['ko'],
        priority: 5,
      })
      setJobTitle('')
      setJobScript('')
      await loadDashboard()
    } catch (error) {
      setJobSubmitError(error instanceof Error ? error.message : 'Job 생성 실패')
    } finally {
      setJobSubmitting(false)
    }
  }

  const handleCancelJob = async (jobId: number) => {
    setJobActionError(null)
    setJobActionLoadingId(jobId)
    try {
      await cancelJob(token, jobId)
      await loadDashboard()
    } catch (error) {
      setJobActionError(error instanceof Error ? error.message : 'Job 취소 실패')
    } finally {
      setJobActionLoadingId(null)
    }
  }

  const handleRetryJob = async (jobId: number) => {
    setJobActionError(null)
    setJobActionLoadingId(jobId)
    try {
      await retryJob(token, jobId)
      await loadDashboard()
    } catch (error) {
      setJobActionError(error instanceof Error ? error.message : 'Job 재시도 실패')
    } finally {
      setJobActionLoadingId(null)
    }
  }

  const handlePublishYoutube = async (jobId: number) => {
    setJobActionError(null)
    setJobPublishMessage(null)
    setJobActionLoadingId(jobId)
    try {
      await publishJobToYoutube(token, jobId, { privacy_status: 'private' })
      setJobPublishMessage(`Job #${jobId} YouTube 게시 요청 완료`)
      await loadDashboard()
    } catch (error) {
      setJobActionError(error instanceof Error ? error.message : 'YouTube 게시 실패')
    } finally {
      setJobActionLoadingId(null)
    }
  }

  const handlePublishTiktok = async (jobId: number) => {
    setJobActionError(null)
    setJobPublishMessage(null)
    setJobActionLoadingId(jobId)
    try {
      await publishJobToTiktok(token, jobId, { headless: true })
      setJobPublishMessage(`Job #${jobId} TikTok 게시 요청 완료`)
      await loadDashboard()
    } catch (error) {
      setJobActionError(error instanceof Error ? error.message : 'TikTok 게시 실패')
    } finally {
      setJobActionLoadingId(null)
    }
  }

  const handleCreateQuota = async (event: FormEvent) => {
    event.preventDefault()
    setQuotaMessage(null)
    if (!quotaPlatformId) {
      setQuotaMessage('플랫폼을 선택해주세요.')
      return
    }
    try {
      await createUploadQuota(token, {
        platform_id: quotaPlatformId,
        daily_limit: Number(quotaDaily || '0'),
        weekly_limit: Number(quotaWeekly || '0'),
        monthly_limit: Number(quotaMonthly || '0'),
      })
      setQuotaMessage('할당량 생성 완료')
      await loadDashboard()
    } catch (error) {
      setQuotaMessage(error instanceof Error ? error.message : '할당량 생성 실패')
    }
  }

  const handleExpandQuota = async (quotaId: number) => {
    setQuotaMessage(null)
    try {
      const target = quotas.find((q) => q.id === quotaId)
      if (!target) {
        return
      }
      await updateUploadQuota(token, quotaId, {
        daily_limit: target.daily_limit + 1,
        weekly_limit: target.weekly_limit + 5,
        monthly_limit: target.monthly_limit + 20,
      })
      setQuotaMessage(`Quota #${quotaId} 상향 완료`)
      await loadDashboard()
    } catch (error) {
      setQuotaMessage(error instanceof Error ? error.message : '할당량 수정 실패')
    }
  }

  const handleDeleteQuota = async (quotaId: number) => {
    if (!confirm('정말로 이 할당량을 삭제하시겠습니까?')) {
      return
    }
    setQuotaMessage(null)
    try {
      await deleteUploadQuota(token, quotaId)
      setQuotaMessage(`Quota #${quotaId} 삭제 완료`)
      await loadDashboard()
    } catch (error) {
      setQuotaMessage(error instanceof Error ? error.message : '할당량 삭제 실패')
    }
  }

  const handleResetQuotas = async (resetType: 'daily' | 'weekly' | 'monthly') => {
    if (!confirm(`정말로 ${resetType} 할당량을 초기화하시겠습니까?`)) {
      return
    }
    setQuotaMessage(null)
    try {
      let result
      if (resetType === 'daily') {
        result = await resetDailyQuotas(token)
      } else if (resetType === 'weekly') {
        result = await resetWeeklyQuotas(token)
      } else {
        result = await resetMonthlyQuotas(token)
      }
      setQuotaMessage(`${resetType} 할당량 초기화 완료 (${result.reset_count}개)`)
      await loadDashboard()
    } catch (error) {
      setQuotaMessage(error instanceof Error ? error.message : '할당량 초기화 실패')
    }
  }

  const handleAgentDiskCleanup = async (agentId: number) => {
    setAgentActionError(null)
    setAgentActionLoadingId(agentId)
    try {
      await recordAgentDiskCleanup(token, agentId)
      await loadDashboard()
    } catch (error) {
      setAgentActionError(error instanceof Error ? error.message : 'Agent 정리 기록 실패')
    } finally {
      setAgentActionLoadingId(null)
    }
  }

  const handleLogout = () => {
    onLogout()
    navigate('/login', { replace: true })
  }

  const handleCreateCredential = async (event: FormEvent) => {
    event.preventDefault()
    setCredentialMessage(null)
    if (!credentialPlatformId) {
      setCredentialMessage('플랫폼을 선택해주세요.')
      return
    }

    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(credentialJson) as Record<string, unknown>
    } catch {
      setCredentialMessage('Credential JSON 형식이 올바르지 않습니다.')
      return
    }

    setCredentialLoading(true)
    try {
      await createCredential(token, {
        platform_id: credentialPlatformId,
        credential_name: credentialName.trim() || undefined,
        credentials: parsed,
        is_default: false,
      })
      setCredentialMessage('Credential 생성 완료')
      await loadDashboard()
    } catch (error) {
      setCredentialMessage(error instanceof Error ? error.message : 'Credential 생성 실패')
    } finally {
      setCredentialLoading(false)
    }
  }

  const handleStartYoutubeOAuth = async () => {
    setOauthMessage(null)
    const youtubePlatform = platforms.find((p) => p.platform_code === 'youtube')
    if (!youtubePlatform) {
      setOauthMessage('YouTube 플랫폼을 찾지 못했습니다.')
      return
    }

    try {
      const redirectUri = `${window.location.origin}/oauth/youtube/callback`
      const result = await startYoutubeOAuth(token, youtubePlatform.id, redirectUri)
      setOauthState(result.state)
      window.open(result.authorization_url, '_blank', 'noopener,noreferrer')
      setOauthMessage('YouTube 인증 페이지를 새 창으로 열었습니다.')
    } catch (error) {
      setOauthMessage(error instanceof Error ? error.message : 'OAuth 시작 실패')
    }
  }

  const handleCompleteYoutubeOAuth = async (event: FormEvent) => {
    event.preventDefault()
    setOauthMessage(null)
    const youtubePlatform = platforms.find((p) => p.platform_code === 'youtube')
    if (!youtubePlatform) {
      setOauthMessage('YouTube 플랫폼을 찾지 못했습니다.')
      return
    }

    if (!oauthCode.trim() || !oauthState.trim()) {
      setOauthMessage('code/state를 모두 입력해주세요.')
      return
    }

    try {
      await completeYoutubeOAuth(oauthCode.trim(), oauthState.trim(), youtubePlatform.id)
      setOauthMessage('YouTube OAuth 콜백 처리 완료')
      setOauthCode('')
      await loadDashboard()
    } catch (error) {
      setOauthMessage(error instanceof Error ? error.message : 'OAuth 콜백 처리 실패')
    }
  }

  const handleCollectTrends = async () => {
    setTrendMessage(null)
    setTrendLoading(true)
    try {
      await collectTrends(token, trendRegion.trim() || 'KR', ['youtube', 'youtube_shorts', 'tiktok'])
      setTrendMessage('트렌드 수집 완료')
      await loadDashboard()
    } catch (error) {
      setTrendMessage(error instanceof Error ? error.message : '트렌드 수집 실패')
    } finally {
      setTrendLoading(false)
    }
  }

  const handleGenerateScript = async (event: FormEvent) => {
    event.preventDefault()
    setScriptMessage(null)
    if (!scriptTopic.trim()) {
      setScriptMessage('주제를 입력해주세요.')
      return
    }

    setScriptLoading(true)
    try {
      await generateScript(token, {
        topic: scriptTopic.trim(),
        trend_id: scriptTrendId ? Number(scriptTrendId) : undefined,
        target_audience: '20-30대',
        platform: 'youtube_shorts',
        language: 'ko',
        duration: 60,
      })
      setScriptMessage('스크립트 생성 완료')
      setScriptTopic('')
      await loadDashboard()
    } catch (error) {
      setScriptMessage(error instanceof Error ? error.message : '스크립트 생성 실패')
    } finally {
      setScriptLoading(false)
    }
  }

  return (
    <div className="page dashboard-page">
      <header className="topbar">
        <h1>Admin Dashboard</h1>
        <div className="topbar-right">
          <span className={wsConnected ? 'ws-badge ws-on' : 'ws-badge ws-off'}>
            {wsConnected ? 'WS 연결됨' : 'WS 끊김'}
          </span>
          <span className="muted">{username}</span>
          <button onClick={() => void loadDashboard()}>새로고침</button>
          <button onClick={handleLogout}>로그아웃</button>
        </div>
      </header>

      {lastRealtimeEvent && <p className="muted">실시간 이벤트: {lastRealtimeEvent}</p>}

      <section className="card health-card">
        <h2>API 상태</h2>
        {loading && <p>상태 조회 중...</p>}

        {!loading && errorMessage && (
          <p className="error">연결 실패: {errorMessage}</p>
        )}

        {!loading && health && (
          <ul className="status-list">
            <li>
              <strong>전체 상태</strong>
              <span>{health.status}</span>
            </li>
            <li>
              <strong>Database</strong>
              <span>{health.database}</span>
            </li>
            <li>
              <strong>Redis</strong>
              <span>{health.redis}</span>
            </li>
            <li>
              <strong>API</strong>
              <span>{health.services.api}</span>
            </li>
          </ul>
        )}
      </section>

      <section className="summary-grid">
        <article className="card summary-card">
          <h2>Agent 현황</h2>
          {loading && <p>조회 중...</p>}
          {!loading && agentStats && (
            <ul className="status-list">
              <li>
                <strong>총 Agent</strong>
                <span>{agentStats.total}</span>
              </li>
              <li>
                <strong>Online</strong>
                <span>{agentStats.online_count}</span>
              </li>
              <li>
                <strong>Offline</strong>
                <span>{agentStats.offline_count}</span>
              </li>
            </ul>
          )}
        </article>

        <article className="card summary-card">
          <h2>Job 현황</h2>
          {loading && <p>조회 중...</p>}
          {!loading && jobStats && (
            <ul className="status-list">
              <li>
                <strong>총 Job</strong>
                <span>{jobStats.total}</span>
              </li>
              <li>
                <strong>대기</strong>
                <span>{jobStats.pending_count}</span>
              </li>
              <li>
                <strong>처리중</strong>
                <span>{jobStats.processing_count}</span>
              </li>
              <li>
                <strong>완료/실패</strong>
                <span>
                  {jobStats.completed_count}/{jobStats.failed_count}
                </span>
              </li>
            </ul>
          )}
        </article>
      </section>

      <section className="summary-grid">
        <article className="card summary-card">
          <h2>최근 Agent (최대 5건)</h2>
          {loading && <p>조회 중...</p>}
          {!loading && agents.length === 0 && <p className="muted">등록된 Agent가 없습니다.</p>}
          {agentActionError && <p className="error">{agentActionError}</p>}
          {!loading && agents.length > 0 && (
            <ul className="status-list">
              {agents.map((agent) => (
                <li key={agent.id}>
                  <div className="job-item-main">
                    <strong>{agent.device_name}</strong>
                    <span>
                      {agent.status}
                      {typeof agent.disk_usage_percent === 'number'
                        ? ` · 디스크 ${agent.disk_usage_percent}%`
                        : ''}
                    </span>
                  </div>
                  <div className="job-actions">
                    <button
                      className="btn-secondary"
                      onClick={() => void handleAgentDiskCleanup(agent.id)}
                      disabled={agentActionLoadingId === agent.id}
                    >
                      {agentActionLoadingId === agent.id ? '처리 중...' : '정리 기록'}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="card summary-card">
          <h2>최근 Job (최대 5건)</h2>
          {loading && <p>조회 중...</p>}
          {!loading && jobs.length === 0 && <p className="muted">생성된 Job이 없습니다.</p>}
          {jobActionError && <p className="error">{jobActionError}</p>}
          {jobPublishMessage && <p className="muted">{jobPublishMessage}</p>}
          {!loading && jobs.length > 0 && (
            <ul className="status-list">
              {jobs.map((job) => (
                <li key={job.id}>
                  <div className="job-item-main">
                    <strong>#{job.id} {job.title}</strong>
                    <span>{job.status}</span>
                  </div>
                  <div className="job-actions">
                    {job.status === 'failed' ? (
                      <button
                        className="btn-secondary"
                        onClick={() => void handleRetryJob(job.id)}
                        disabled={jobActionLoadingId === job.id}
                      >
                        {jobActionLoadingId === job.id ? '처리 중...' : '재시도'}
                      </button>
                    ) : job.status === 'completed' ? (
                      <>
                        <button
                          className="btn-secondary"
                          onClick={() => void handlePublishYoutube(job.id)}
                          disabled={jobActionLoadingId === job.id}
                        >
                          {jobActionLoadingId === job.id ? '처리 중...' : 'YouTube 게시'}
                        </button>
                        <button
                          className="btn-secondary"
                          onClick={() => void handlePublishTiktok(job.id)}
                          disabled={jobActionLoadingId === job.id}
                        >
                          {jobActionLoadingId === job.id ? '처리 중...' : 'TikTok 게시'}
                        </button>
                      </>
                    ) : (
                      <button
                        className="btn-secondary"
                        onClick={() => void handleCancelJob(job.id)}
                        disabled={
                          jobActionLoadingId === job.id ||
                          job.status === 'completed'
                        }
                      >
                        {jobActionLoadingId === job.id ? '처리 중...' : '취소'}
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <section className="card">
        <h2>Job 생성</h2>
        <form onSubmit={handleCreateJob} className="form-stack">
          <label htmlFor="job-platform">플랫폼</label>
          <select
            id="job-platform"
            value={selectedPlatformId ?? ''}
            onChange={(event) => setSelectedPlatformId(Number(event.target.value))}
          >
            {platforms.map((platform) => (
              <option key={platform.id} value={platform.id}>
                {platform.platform_name}
              </option>
            ))}
          </select>

          <label htmlFor="job-title">제목</label>
          <input
            id="job-title"
            value={jobTitle}
            onChange={(event) => setJobTitle(event.target.value)}
            placeholder="예: 오늘의 AI 트렌드"
          />

          <label htmlFor="job-script">스크립트</label>
          <textarea
            id="job-script"
            value={jobScript}
            onChange={(event) => setJobScript(event.target.value)}
            placeholder="쇼츠 스크립트를 입력하세요"
            rows={5}
          />

          {jobSubmitError && <p className="error">{jobSubmitError}</p>}

          <button type="submit" disabled={jobSubmitting}>
            {jobSubmitting ? '생성 중...' : 'Job 생성'}
          </button>
        </form>
      </section>

      <section className="summary-grid">
        <article className="card summary-card">
          <h2>Credentials</h2>
          <form onSubmit={handleCreateCredential} className="form-stack">
            <label htmlFor="cred-platform">플랫폼</label>
            <select
              id="cred-platform"
              value={credentialPlatformId ?? ''}
              onChange={(event) => setCredentialPlatformId(Number(event.target.value))}
            >
              {platforms.map((platform) => (
                <option key={platform.id} value={platform.id}>
                  {platform.platform_name}
                </option>
              ))}
            </select>

            <label htmlFor="cred-name">Credential 이름</label>
            <input
              id="cred-name"
              value={credentialName}
              onChange={(event) => setCredentialName(event.target.value)}
              placeholder="예: YouTube 메인"
            />

            <label htmlFor="cred-json">Credential JSON</label>
            <textarea
              id="cred-json"
              value={credentialJson}
              onChange={(event) => setCredentialJson(event.target.value)}
              rows={4}
            />

            <button type="submit" disabled={credentialLoading}>
              {credentialLoading ? '생성 중...' : 'Credential 생성'}
            </button>
          </form>

          <div className="form-stack">
            <button className="btn-secondary" onClick={() => void handleStartYoutubeOAuth()}>
              YouTube OAuth 시작
            </button>
            <form onSubmit={handleCompleteYoutubeOAuth} className="form-stack">
              <input
                value={oauthState}
                onChange={(event) => setOauthState(event.target.value)}
                placeholder="OAuth state"
              />
              <input
                value={oauthCode}
                onChange={(event) => setOauthCode(event.target.value)}
                placeholder="OAuth code"
              />
              <button type="submit">OAuth 콜백 처리</button>
            </form>
            {oauthMessage && <p className="muted">{oauthMessage}</p>}
          </div>

          {credentialMessage && <p className="muted">{credentialMessage}</p>}

          <ul className="status-list">
            {credentials.slice(0, 5).map((cred) => (
              <li key={cred.id}>
                <div className="job-item-main">
                  <strong>{cred.credential_name ?? `Credential #${cred.id}`}</strong>
                  <span>{cred.status} · platform_id={cred.platform_id}</span>
                </div>
              </li>
            ))}
          </ul>
        </article>

        <article className="card summary-card">
          <h2>Trends</h2>
          <div className="form-stack">
            <label htmlFor="trend-region">Region</label>
            <input
              id="trend-region"
              value={trendRegion}
              onChange={(event) => setTrendRegion(event.target.value.toUpperCase())}
              placeholder="KR"
            />
            <button onClick={() => void handleCollectTrends()} disabled={trendLoading}>
              {trendLoading ? '수집 중...' : '트렌드 수집'}
            </button>
            {trendMessage && <p className="muted">{trendMessage}</p>}
          </div>

          <ul className="status-list">
            {trends.slice(0, 8).map((trend) => (
              <li key={trend.id}>
                <div className="job-item-main">
                  <strong>{trend.keyword}</strong>
                  <span>{trend.source} · 점수 {trend.trend_score.toFixed(1)}</span>
                </div>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="card">
        <h2>Scripts</h2>
        <form onSubmit={handleGenerateScript} className="form-stack">
          <label htmlFor="script-topic">주제</label>
          <input
            id="script-topic"
            value={scriptTopic}
            onChange={(event) => setScriptTopic(event.target.value)}
            placeholder="예: 2026 AI 자동화 트렌드"
          />

          <label htmlFor="script-trend-id">Trend ID (선택)</label>
          <input
            id="script-trend-id"
            value={scriptTrendId}
            onChange={(event) => setScriptTrendId(event.target.value)}
            placeholder="예: 1"
          />

          <button type="submit" disabled={scriptLoading}>
            {scriptLoading ? '생성 중...' : '스크립트 생성'}
          </button>
          {scriptMessage && <p className="muted">{scriptMessage}</p>}
        </form>

        <ul className="status-list">
          {scripts.slice(0, 8).map((script) => (
            <li key={script.id}>
              <div className="job-item-main">
                <strong>#{script.id} {script.title}</strong>
                <span>품질 {script.quality_score.toFixed(1)} · 바이럴 {script.viral_potential.toFixed(1)}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>Upload Quotas</h2>
        <form onSubmit={handleCreateQuota} className="form-stack">
          <label htmlFor="quota-platform">플랫폼</label>
          <select
            id="quota-platform"
            value={quotaPlatformId ?? ''}
            onChange={(event) => setQuotaPlatformId(Number(event.target.value))}
          >
            {platforms.map((platform) => (
              <option key={platform.id} value={platform.id}>{platform.platform_name}</option>
            ))}
          </select>

          <label htmlFor="quota-daily">일일</label>
          <input id="quota-daily" value={quotaDaily} onChange={(e) => setQuotaDaily(e.target.value)} />

          <label htmlFor="quota-weekly">주간</label>
          <input id="quota-weekly" value={quotaWeekly} onChange={(e) => setQuotaWeekly(e.target.value)} />

          <label htmlFor="quota-monthly">월간</label>
          <input id="quota-monthly" value={quotaMonthly} onChange={(e) => setQuotaMonthly(e.target.value)} />

          <button type="submit">할당량 생성</button>
        </form>
        
        <div className="form-stack">
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button className="btn-secondary" onClick={() => void handleResetQuotas('daily')}>
              Daily 초기화
            </button>
            <button className="btn-secondary" onClick={() => void handleResetQuotas('weekly')}>
              Weekly 초기화
            </button>
            <button className="btn-secondary" onClick={() => void handleResetQuotas('monthly')}>
              Monthly 초기화
            </button>
          </div>
        </div>
        
        {quotaMessage && <p className="muted">{quotaMessage}</p>}

        <ul className="status-list">
          {quotas.map((quota) => (
            <li key={quota.id}>
              <div className="job-item-main">
                <strong>platform_id={quota.platform_id} · D/W/M {quota.daily_limit}/{quota.weekly_limit}/{quota.monthly_limit}</strong>
                <span>사용 {quota.used_today}/{quota.used_week}/{quota.used_month}</span>
              </div>
              <div className="job-actions">
                <button className="btn-secondary" onClick={() => void handleExpandQuota(quota.id)}>
                  상향
                </button>
                <button className="btn-danger" onClick={() => void handleDeleteQuota(quota.id)}>
                  삭제
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

export default DashboardPage
