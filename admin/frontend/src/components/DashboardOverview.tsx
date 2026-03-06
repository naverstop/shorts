import { useEffect, useState } from 'react'
import { fetchHealth, fetchAgentStats, fetchJobStats, type HealthResponse, type AgentStatsResponse, type JobStatsResponse } from '../services/api'
import './DashboardOverview.css'

export type DashboardOverviewProps = {
  token: string
}

export function DashboardOverview({ token }: DashboardOverviewProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [agentStats, setAgentStats] = useState<AgentStatsResponse | null>(null)
  const [jobStats, setJobStats] = useState<JobStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    void loadData()
  }, [token])

  async function loadData() {
    setLoading(true)
    try {
      const [healthData, agentData, jobData] = await Promise.all([
        fetchHealth(),
        fetchAgentStats(token),
        fetchJobStats(token),
      ])
      setHealth(healthData)
      setAgentStats(agentData)
      setJobStats(jobData)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="dashboard-overview">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>대시보드를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-overview">
      {/* Page Header */}
      <div className="page-header">
        <h1>대시보드</h1>
        <p className="page-subtitle">쇼츠 영상 자동화 시스템 현황</p>
      </div>

      {/* System Health Status */}
      <section className="section">
        <h2 className="section-title">📊 시스템 상태</h2>
        <div className="status-grid">
          <div className={`status-card ${health?.status === 'healthy' ? 'status-healthy' : 'status-unhealthy'}`}>
            <div className="status-icon">
              {health?.status === 'healthy' ? '✅' : '⚠️'}
            </div>
            <div className="status-content">
              <div className="status-label">전체 상태</div>
              <div className="status-value">{health?.status || 'unknown'}</div>
            </div>
          </div>

          <div className={`status-card ${health?.database === 'connected' ? 'status-healthy' : 'status-unhealthy'}`}>
            <div className="status-icon">🗄️</div>
            <div className="status-content">
              <div className="status-label">Database</div>
              <div className="status-value">{health?.database || 'unknown'}</div>
            </div>
          </div>

          <div className={`status-card ${health?.redis === 'connected' ? 'status-healthy' : 'status-unhealthy'}`}>
            <div className="status-icon">⚡</div>
            <div className="status-content">
              <div className="status-label">Redis</div>
              <div className="status-value">{health?.redis || 'unknown'}</div>
            </div>
          </div>

          <div className={`status-card ${health?.services?.api === 'running' ? 'status-healthy' : 'status-unhealthy'}`}>
            <div className="status-icon">🔌</div>
            <div className="status-content">
              <div className="status-label">API</div>
              <div className="status-value">{health?.services?.api || 'unknown'}</div>
            </div>
          </div>
        </div>
      </section>

      {/* Statistics Cards */}
      <section className="section">
        <h2 className="section-title">📈 실시간 통계</h2>
        <div className="stats-grid">
          {/* Agent Stats */}
          <div className="stat-card agent-card">
            <div className="stat-header">
              <span className="stat-icon">🤖</span>
              <h3>Agent 현황</h3>
            </div>
            <div className="stat-body">
              <div className="stat-main">
                <div className="stat-number">{agentStats?.total || 0}</div>
                <div className="stat-label">총 Agent</div>
              </div>
              <div className="stat-details">
                <div className="stat-item">
                  <span className="stat-dot online"></span>
                  <span>Online: {agentStats?.online_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-dot offline"></span>
                  <span>Offline: {agentStats?.offline_count || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Job Stats */}
          <div className="stat-card job-card">
            <div className="stat-header">
              <span className="stat-icon">📋</span>
              <h3>Job 현황</h3>
            </div>
            <div className="stat-body">
              <div className="stat-main">
                <div className="stat-number">{jobStats?.total || 0}</div>
                <div className="stat-label">총 Job</div>
              </div>
              <div className="stat-details">
                <div className="stat-item">
                  <span className="stat-dot pending"></span>
                  <span>대기: {jobStats?.pending_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-dot processing"></span>
                  <span>처리중: {jobStats?.processing_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-dot completed"></span>
                  <span>완료: {jobStats?.completed_count || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-dot failed"></span>
                  <span>실패: {jobStats?.failed_count || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Process Timeline */}
      <section className="section">
        <h2 className="section-title">🔄 프로세스 진행 현황</h2>
        <div className="process-timeline">
          <div className={`timeline-step ${agentStats && agentStats.online_count > 0 ? 'completed' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-content">
              <div className="step-title">Agent 등록</div>
              <div className="step-desc">
                {agentStats && agentStats.total > 0
                  ? `${agentStats.total}개 Agent 등록 완료`
                  : 'Agent를 등록하세요'}
              </div>
            </div>
          </div>

          <div className="timeline-connector"></div>

          <div className={`timeline-step ${jobStats && jobStats.total > 0 ? 'completed' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-content">
              <div className="step-title">Job 생성</div>
              <div className="step-desc">
                {jobStats && jobStats.total > 0
                  ? `${jobStats.total}개 Job 생성됨`
                  : 'Job을 생성하세요'}
              </div>
            </div>
          </div>

          <div className="timeline-connector"></div>

          <div className={`timeline-step ${jobStats && jobStats.processing_count > 0 ? 'active' : jobStats && jobStats.completed_count > 0 ? 'completed' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-content">
              <div className="step-title">영상 처리</div>
              <div className="step-desc">
                {jobStats && jobStats.processing_count > 0
                  ? `${jobStats.processing_count}개 처리 중`
                  : jobStats && jobStats.completed_count > 0
                  ? `${jobStats.completed_count}개 처리 완료`
                  : '대기 중'}
              </div>
            </div>
          </div>

          <div className="timeline-connector"></div>

          <div className={`timeline-step ${jobStats && jobStats.completed_count > 0 ? 'completed' : ''}`}>
            <div className="step-number">4</div>
            <div className="step-content">
              <div className="step-title">플랫폼 게시</div>
              <div className="step-desc">
                {jobStats && jobStats.completed_count > 0
                  ? '게시 준비 완료'
                  : '영상 완료 후 게시'}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="section">
        <h2 className="section-title">⚡ 빠른 작업</h2>
        <div className="quick-actions">
          <button className="action-btn primary-btn">
            <span className="btn-icon">➕</span>
            <span>새 Job 생성</span>
          </button>
          <button className="action-btn secondary-btn">
            <span className="btn-icon">🔄</span>
            <span>트렌드 수집</span>
          </button>
          <button className="action-btn secondary-btn">
            <span className="btn-icon">📊</span>
            <span>할당량 관리</span>
          </button>
          <button className="action-btn secondary-btn" onClick={() => void loadData()}>
            <span className="btn-icon">↻</span>
            <span>새로고침</span>
          </button>
        </div>
      </section>
    </div>
  )
}
