import { useEffect, useState } from 'react'
import { fetchAgents, fetchAgentStats, recordAgentDiskCleanup, type AgentItem, type AgentStatsResponse } from '../services/api'
import '../components/SectionStyles.css'

export type AgentsSectionProps = {
  token: string
  username: string
}

export function AgentsSection({ token, username }: AgentsSectionProps) {
  const [agents, setAgents] = useState<AgentItem[]>([])
  const [stats, setStats] = useState<AgentStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  useEffect(() => {
    void loadData()
  }, [token])

  async function loadData() {
    setLoading(true)
    try {
      const [agentsData, statsData] = await Promise.all([
        fetchAgents(token),
        fetchAgentStats(token),
      ])
      setAgents(agentsData)
      setStats(statsData)
      setMessage(null)
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Agent 정보 조회 실패' })
    } finally {
      setLoading(false)
    }
  }

  const handleDiskCleanup = async (agentId: number) => {
    if (!confirm('Agent의 디스크 정리를 기록하시겠습니까?')) {
      return
    }

    setActionLoading(agentId)
    try {
      await recordAgentDiskCleanup(token, agentId)
      setMessage({ type: 'success', text: `Agent #${agentId} 디스크 정리 기록 완료` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '디스크 정리 기록 실패' })
    } finally {
      setActionLoading(null)
    }
  }

  const handleAssignToUser = async (_agentId: number) => {
    if (!confirm(`Agent를 현재 사용자(${username})에게 할당하시겠습니까?`)) {
      return
    }

    // TODO: Implement user-agent assignment API
    setMessage({ type: 'success', text: '사용자-Agent 매칭 기능은 곧 지원될 예정입니다.' })
  }

  return (
    <div className="section-page">
      {/* Header */}
      <div className="section-header">
        <div>
          <h1>🤖 Agent 관리</h1>
          <p className="section-subtitle">등록된 Agent 목록 및 관리</p>
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

      {/* Stats */}
      {stats && (
        <div className="stats-mini-grid">
          <div className="stat-mini-card">
            <div className="stat-mini-value">{stats.total}</div>
            <div className="stat-mini-label">총 Agent</div>
          </div>
          <div className="stat-mini-card">
            <div className="stat-mini-value">{stats.online_count}</div>
            <div className="stat-mini-label">Online</div>
          </div>
          <div className="stat-mini-card">
            <div className="stat-mini-value">{stats.offline_count}</div>
            <div className="stat-mini-label">Offline</div>
          </div>
        </div>
      )}

      {/* Agent List */}
      <div className="content-card">
        <h2 className="card-title">
          <span className="card-icon">📱</span>
          Agent 목록
        </h2>

        {loading && (
          <div className="empty-state">
            <div className="loading-spinner"></div>
            <p className="empty-state-text">Agent 목록을 불러오는 중...</p>
          </div>
        )}

        {!loading && agents.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">📱</div>
            <p className="empty-state-text">등록된 Agent가 없습니다.</p>
            <p className="empty-state-text">Android 앱을 실행하여 Agent를 등록하세요.</p>
          </div>
        )}

        {!loading && agents.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Device Name</th>
                <th>상태</th>
                <th>디스크 사용량</th>
                <th>마지막 Heartbeat</th>
                <th>사용자</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id}>
                  <td>#{agent.id}</td>
                  <td>
                    <strong>{agent.device_name}</strong>
                  </td>
                  <td>
                    <span className={`status-badge ${agent.status}`}>
                      <span className={`status-dot ${agent.status}`}></span>
                      {agent.status === 'online' ? 'Online' : 'Offline'}
                    </span>
                  </td>
                  <td>
                    {typeof agent.disk_usage_percent === 'number'
                      ? `${agent.disk_usage_percent}%`
                      : '-'}
                  </td>
                  <td>
                    {agent.last_heartbeat
                      ? new Date(agent.last_heartbeat).toLocaleString('ko-KR')
                      : '-'}
                  </td>
                  <td>
                    <span className="status-badge offline">매칭 준비중</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        className="btn btn-secondary"
                        onClick={() => void handleDiskCleanup(agent.id)}
                        disabled={actionLoading === agent.id}
                      >
                        {actionLoading === agent.id ? (
                          <span className="loading-spinner"></span>
                        ) : (
                          '🗑️ 정리'
                        )}
                      </button>
                      <button
                        className="btn btn-primary"
                        onClick={() => void handleAssignToUser(agent.id)}
                      >
                        👤 할당
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Info Card */}
      <div className="content-card">
        <h2 className="card-title">
          <span className="card-icon">ℹ️</span>
          Agent 사용 가이드
        </h2>
        <div style={{ fontSize: '0.875rem', color: '#4b5563', lineHeight: '1.6' }}>
          <p><strong>1. Agent 등록:</strong> Android 앱을 실행하고 Settings에서 Backend URL을 입력한 후 Register 버튼을 클릭하세요.</p>
          <p><strong>2. 자동 작업:</strong> 등록된 Agent는 자동으로 대기 중인 Job을 폴링하여 처리합니다.</p>
          <p><strong>3. 상태 확인:</strong> Agent가 온라인 상태인지 확인하고, 오프라인이면 Android 앱을 재시작하세요.</p>
          <p><strong>4. 디스크 정리:</strong> Agent의 임시 파일을 정리하여 디스크 공간을 확보할 수 있습니다.</p>
          <p><strong>5. 사용자 할당:</strong> Agent를 특정 사용자에게 할당하여 전용으로 사용할 수 있습니다.</p>
        </div>
      </div>
    </div>
  )
}
