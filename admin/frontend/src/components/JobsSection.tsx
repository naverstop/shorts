import { useEffect, useState, type FormEvent } from 'react'
import {
  fetchJobs,
  fetchJobStats,
  fetchPlatforms,
  createJob,
  cancelJob,
  retryJob,
  publishJobToYoutube,
  publishJobToTiktok,
  type JobItem,
  type JobStatsResponse,
  type PlatformItem,
} from '../services/api'
import '../components/SectionStyles.css'

export type JobsSectionProps = {
  token: string
}

type JobCategory = 'shorts' | 'music' | 'product' | 'other'

type AutomationConfig = {
  enabled: boolean
  scheduler_enabled: boolean
  hourly_limit: number
  auto_search: boolean
  auto_summarize: boolean
  auto_generate_script: boolean
  auto_create_video: boolean
  auto_review: boolean
  auto_publish: boolean
}

export function JobsSection({ token }: JobsSectionProps) {
  const [jobs, setJobs] = useState<JobItem[]>([])
  const [stats, setStats] = useState<JobStatsResponse | null>(null)
  const [platforms, setPlatforms] = useState<PlatformItem[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Automation config
  const [automation, setAutomation] = useState<AutomationConfig>({
    enabled: false,
    scheduler_enabled: false,
    hourly_limit: 5,
    auto_search: true,
    auto_summarize: true,
    auto_generate_script: true,
    auto_create_video: true,
    auto_review: false,
    auto_publish: false,
  })

  // Filter
  const [categoryFilter, setCategoryFilter] = useState<JobCategory | 'all'>('all')

  // Form state
  const [platformId, setPlatformId] = useState<number | null>(null)
  const [title, setTitle] = useState('')
  const [script, setScript] = useState('')
  const [priority, setPriority] = useState('5')
  const [category, setCategory] = useState<JobCategory>('shorts')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    void loadData()
  }, [token])

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [message])

  async function loadData() {
    setLoading(true)
    try {
      const [jobsData, statsData, platformsData] = await Promise.all([
        fetchJobs(token),
        fetchJobStats(token),
        fetchPlatforms(),
      ])
      setJobs(jobsData)
      setStats(statsData)
      setPlatforms(platformsData)
      setMessage(null)
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Job 정보 조회 실패' })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setMessage(null)

    if (!platformId || !title.trim() || !script.trim()) {
      setMessage({ type: 'error', text: '플랫폼, 제목, 스크립트를 모두 입력해주세요.' })
      return
    }

    setSubmitting(true)
    try {
      await createJob(token, {
        platform_id: platformId,
        title: title.trim(),
        script: script.trim(),
        source_language: 'ko',
        target_languages: ['ko'],
        priority: Number(priority),
      })
      setMessage({ type: 'success', text: 'Job 생성 완료!' })
      setTitle('')
      setScript('')
      setPriority('5')
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Job 생성 실패' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = async (jobId: number) => {
    if (!confirm(`Job #${jobId}를 취소하시겠습니까?`)) {
      return
    }

    setActionLoading(jobId)
    try {
      await cancelJob(token, jobId)
      setMessage({ type: 'success', text: `Job #${jobId} 취소 완료` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Job 취소 실패' })
    } finally {
      setActionLoading(null)
    }
  }

  const handleRetry = async (jobId: number) => {
    setActionLoading(jobId)
    try {
      await retryJob(token, jobId)
      setMessage({ type: 'success', text: `Job #${jobId} 재시도 시작` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Job 재시도 실패' })
    } finally {
      setActionLoading(null)
    }
  }

  const handlePublishYoutube = async (jobId: number) => {
    if (!confirm(`Job #${jobId}를 YouTube에 게시하시겠습니까?`)) {
      return
    }

    setActionLoading(jobId)
    try {
      await publishJobToYoutube(token, jobId, { privacy_status: 'private' })
      setMessage({ type: 'success', text: `Job #${jobId} YouTube 게시 요청 완료` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'YouTube 게시 실패' })
    } finally {
      setActionLoading(null)
    }
  }

  const handlePublishTiktok = async (jobId: number) => {
    if (!confirm(`Job #${jobId}를 TikTok에 게시하시겠습니까?`)) {
      return
    }

    setActionLoading(jobId)
    try {
      await publishJobToTiktok(token, jobId, { headless: true })
      setMessage({ type: 'success', text: `Job #${jobId} TikTok 게시 요청 완료` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'TikTok 게시 실패' })
    } finally {
      setActionLoading(null)
    }
  }

  const handleToggleAutomation = (key: keyof AutomationConfig) => {
    setAutomation((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="section-page">
      {/* Header */}
      <div className="section-header">
        <div>
          <h1>📋 Job 관리</h1>
          <p className="section-subtitle">완전 자동화 영상 제작 및 배포 관리</p>
        </div>
        <div className="section-actions">
          <button className="btn btn-secondary" onClick={() => void loadData()}>
            <span className="btn-icon">↻</span>
            새로고침
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* Automation Control Panel */}
      <div className="content-card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <h2 className="card-title" style={{ color: 'white' }}>
          <span className="card-icon">🤖</span>
          자동화 설정
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
          {/* Master Switch */}
          <div style={{ background: 'rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>🔧 전체 자동화</strong>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={automation.enabled}
                  onChange={() => handleToggleAutomation('enabled')}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
            <small style={{ opacity: 0.9 }}>모든 자동화 프로세스 ON/OFF</small>
          </div>

          {/* Scheduler */}
          <div style={{ background: 'rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>⏰ 스케줄러</strong>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={automation.scheduler_enabled}
                  onChange={() => handleToggleAutomation('scheduler_enabled')}
                  disabled={!automation.enabled}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
            <small style={{ opacity: 0.9 }}>시간당 {automation.hourly_limit}개 Job 자동 생성</small>
          </div>
        </div>

        {/* Workflow Steps */}
        <div style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>📊 워크플로우 단계별 설정</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem' }}>
            {[
              { key: 'auto_search', label: '1️⃣ 인기영상 검색', desc: 'YouTube/TikTok 트렌드' },
              { key: 'auto_summarize', label: '2️⃣ Text 요약', desc: 'Google Gemini' },
              { key: 'auto_generate_script', label: '3️⃣ 스크립트 생성', desc: 'Claude AI' },
              { key: 'auto_create_video', label: '4️⃣ 영상 생성', desc: 'Agent 처리' },
              { key: 'auto_review', label: '5️⃣ 영상 검토', desc: '품질 검증' },
              { key: 'auto_publish', label: '6️⃣ 영상 배포', desc: '플랫폼 업로드' },
            ].map((step) => (
              <div
                key={step.key}
                style={{
                  background: 'rgba(255,255,255,0.15)',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                  <strong style={{ fontSize: '0.8rem' }}>{step.label}</strong>
                  <label className="toggle-switch" style={{ transform: 'scale(0.8)' }}>
                    <input
                      type="checkbox"
                      checked={automation[step.key as keyof AutomationConfig] as boolean}
                      onChange={() => handleToggleAutomation(step.key as keyof AutomationConfig)}
                      disabled={!automation.enabled}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
                <small style={{ opacity: 0.8, fontSize: '0.75rem' }}>{step.desc}</small>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.1)', borderRadius: '6px' }}>
          <small>
            <strong>💡 자동화 프로세스:</strong> 트렌드 분석 → 대상 선정 → 요약 → 스크립트 생성 → 영상 제작 → 검토 → 배포
          </small>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="stats-mini-grid">
          <div className="stat-mini-card">
            <div className="stat-mini-value">{stats.total}</div>
            <div className="stat-mini-label">총 Job</div>
          </div>
          <div className="stat-mini-card">
            <div className="stat-mini-value">{stats.pending_count}</div>
            <div className="stat-mini-label">대기</div>
          </div>
          <div className="stat-mini-card">
            <div className="stat-mini-value">{stats.processing_count}</div>
            <div className="stat-mini-label">처리중</div>
          </div>
          <div className="stat-mini-card">
            <div className="stat-mini-value">{stats.completed_count}</div>
            <div className="stat-mini-label">완료</div>
          </div>
        </div>
      )}

      {/* Category Filter */}
      <div className="content-card">
        <h3>🏷️ 카테고리 필터</h3>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
          {[
            { value: 'all', label: '전체', icon: '📁' },
            { value: 'shorts', label: '쇼츠', icon: '📱' },
            { value: 'music', label: '음악', icon: '🎵' },
            { value: 'product', label: '상품영상', icon: '🛍️' },
            { value: 'other', label: '기타', icon: '📦' },
          ].map((cat) => (
            <button
              key={cat.value}
              className={`btn ${categoryFilter === cat.value ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setCategoryFilter(cat.value as JobCategory | 'all')}
            >
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Create Job Form */}
      <div className="content-card">
        <h2 className="card-title">
          <span className="card-icon">➕</span>
          새 Job 생성 (수동)
        </h2>

        <form onSubmit={(e) => void handleSubmit(e)}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">플랫폼 *</label>
              <select
                className="form-select"
                value={platformId || ''}
                onChange={(e) => setPlatformId(Number(e.target.value))}
                required
              >
                <option value="">선택하세요</option>
                {platforms.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.platform_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">카테고리</label>
              <select
                className="form-select"
                value={category}
                onChange={(e) => setCategory(e.target.value as JobCategory)}
              >
                <option value="shorts">📱 쇼츠</option>
                <option value="music">🎵 음악</option>
                <option value="product">🛍️ 상품영상</option>
                <option value="other">📦 기타</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">제목 *</label>
              <input
                type="text"
                className="form-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="영상 제목을 입력하세요"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">우선순위</label>
              <select
                className="form-select"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="1">1 (낮음)</option>
                <option value="3">3</option>
                <option value="5">5 (보통)</option>
                <option value="7">7</option>
                <option value="10">10 (높음)</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">스크립트 *</label>
            <textarea
              className="form-textarea"
              value={script}
              onChange={(e) => setScript(e.target.value)}
              placeholder="영상 스크립트를 입력하세요..."
              rows={6}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? (
              <>
                <span className="loading-spinner"></span>
                생성 중...
              </>
            ) : (
              <>
                <span className="btn-icon">➕</span>
                Job 생성
              </>
            )}
          </button>
        </form>
      </div>

      {/* Job List */}
      <div className="content-card">
        <h2 className="card-title">
          <span className="card-icon">📑</span>
          Job 목록 및 모니터링
        </h2>

        {loading && (
          <div className="empty-state">
            <div className="loading-spinner"></div>
            <p className="empty-state-text">Job 목록을 불러오는 중...</p>
          </div>
        )}

        {!loading && jobs.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">📋</div>
            <p className="empty-state-text">생성된 Job이 없습니다.</p>
            <small>자동화를 활성화하거나 수동으로 Job을 생성하세요.</small>
          </div>
        )}

        {!loading && jobs.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>카테고리</th>
                <th>제목</th>
                <th>플랫폼</th>
                <th>상태</th>
                <th>Agent</th>
                <th>워크플로우</th>
                <th>우선순위</th>
                <th>생성일</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>#{job.id}</td>
                  <td>
                    <span style={{ fontSize: '1.2rem' }}>📱</span>
                  </td>
                  <td>
                    <strong>{job.title}</strong>
                  </td>
                  <td>-</td>
                  <td>
                    <span className={`status-badge ${job.status}`}>
                      {job.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                      미할당
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '2px', fontSize: '0.7rem' }}>
                      <span title="검색">🔍</span>
                      <span title="요약">📄</span>
                      <span title="스크립트">📝</span>
                      <span title="제작">🎬</span>
                      <span title="검토">✅</span>
                      <span title="배포">🚀</span>
                    </div>
                  </td>
                  <td>{job.priority}</td>
                  <td>
                    {job.created_at
                      ? new Date(job.created_at).toLocaleDateString('ko-KR')
                      : '-'}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {job.status === 'pending' && (
                        <button
                          className="btn btn-secondary"
                          onClick={() => void handleCancel(job.id)}
                          disabled={actionLoading === job.id}
                          style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                        >
                          ❌ 취소
                        </button>
                      )}
                      {job.status === 'failed' && (
                        <button
                          className="btn btn-secondary"
                          onClick={() => void handleRetry(job.id)}
                          disabled={actionLoading === job.id}
                          style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                        >
                          🔄 재시도
                        </button>
                      )}
                      {job.status === 'completed' && (
                        <>
                          <button
                            className="btn btn-primary"
                            onClick={() => void handlePublishYoutube(job.id)}
                            disabled={actionLoading === job.id}
                            style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                          >
                            📺 YouTube
                          </button>
                          <button
                            className="btn btn-primary"
                            onClick={() => void handlePublishTiktok(job.id)}
                            disabled={actionLoading === job.id}
                            style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                          >
                            🎵 TikTok
                          </button>
                        </>
                      )}
                      {actionLoading === job.id && (
                        <span className="loading-spinner"></span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Usage Guide */}
      <div className="content-card" style={{ background: '#f8f9fa' }}>
        <h3>💡 자동화 워크플로우 안내</h3>
        <div style={{ lineHeight: '1.8' }}>
          <h4 style={{ fontSize: '0.95rem', marginTop: '1rem' }}>🔄 완전 자동화 프로세스:</h4>
          <ol style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
            <li><strong>트렌드 수집:</strong> YouTube/TikTok에서 인기 영상 검색 및 키워드 추출</li>
            <li><strong>대상 선정:</strong> 트렌드 점수 및 카테고리 기반 후보 선정</li>
            <li><strong>Text 요약:</strong> Google Gemini로 원본 영상 콘텐츠 요약</li>
            <li><strong>스크립트 생성:</strong> Claude AI로 새로운 영상 제작 스크립트 생성 (Hook-Body-CTA)</li>
            <li><strong>Job 생성:</strong> 생성된 스크립트로 자동 Job 생성</li>
            <li><strong>Agent 할당:</strong> 온라인 Agent에게 자동 배포</li>
            <li><strong>영상 제작:</strong> Agent가 영상 렌더링 및 처리</li>
            <li><strong>품질 검토:</strong> AI 기반 품질 검증 (선택적)</li>
            <li><strong>플랫폼 배포:</strong> YouTube/TikTok 자동 업로드</li>
          </ol>

          <h4 style={{ fontSize: '0.95rem', marginTop: '1rem' }}>⚙️ 설정 옵션:</h4>
          <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
            <li><strong>스케줄러:</strong> 시간당 생성할 Job 수 제한 (기본: 5개)</li>
            <li><strong>단계별 On/Off:</strong> 특정 단계만 자동화하거나 건너뛰기 가능</li>
            <li><strong>카테고리 필터:</strong> 원하는 영상 유형만 자동 생성</li>
            <li><strong>수동 개입:</strong> 자동화 비활성화 시 수동 Job 생성 가능</li>
          </ul>

          <h4 style={{ fontSize: '0.95rem', marginTop: '1rem' }}>📊 모니터링:</h4>
          <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
            <li>각 Job의 워크플로우 단계 실시간 확인</li>
            <li>Job-Agent 매칭 상태 추적</li>
            <li>실패한 Job 자동 재시도 또는 수동 재시도</li>
            <li>배포 현황 및 통계 확인</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
