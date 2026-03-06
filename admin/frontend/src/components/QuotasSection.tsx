import { useEffect, useState, type FormEvent } from 'react'
import {
  fetchUploadQuotas,
  fetchPlatforms,
  createUploadQuota,
  deleteUploadQuota,
  resetDailyQuotas,
  resetWeeklyQuotas,
  resetMonthlyQuotas,
  type UploadQuotaItem,
  type PlatformItem,
} from '../services/api'
import '../components/SectionStyles.css'

export type QuotasSectionProps = {
  token: string
}

export function QuotasSection({ token }: QuotasSectionProps) {
  const [quotas, setQuotas] = useState<UploadQuotaItem[]>([])
  const [platforms, setPlatforms] = useState<PlatformItem[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Form state
  const [platformId, setPlatformId] = useState<number | null>(null)
  const [dailyLimit, setDailyLimit] = useState('3')
  const [weeklyLimit, setWeeklyLimit] = useState('15')
  const [monthlyLimit, setMonthlyLimit] = useState('50')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    void loadData()
  }, [token])

  async function loadData() {
    setLoading(true)
    try {
      const [quotasData, platformsData] = await Promise.all([
        fetchUploadQuotas(token),
        fetchPlatforms(),
      ])
      setQuotas(quotasData)
      setPlatforms(platformsData)
      setMessage(null)
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '할당량 조회 실패' })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setMessage(null)

    if (!platformId) {
      setMessage({ type: 'error', text: '플랫폼을 선택해주세요.' })
      return
    }

    setSubmitting(true)
    try {
      await createUploadQuota(token, {
        platform_id: platformId,
        daily_limit: Number(dailyLimit),
        weekly_limit: Number(weeklyLimit),
        monthly_limit: Number(monthlyLimit),
      })
      setMessage({ type: 'success', text: '할당량 생성 완료!' })
      setDailyLimit('3')
      setWeeklyLimit('15')
      setMonthlyLimit('50')
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '할당량 생성 실패' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (quotaId: number) => {
    if (!confirm('정말로 이 할당량을 삭제하시겠습니까?')) {
      return
    }

    try {
      await deleteUploadQuota(token, quotaId)
      setMessage({ type: 'success', text: '할당량 삭제 완료' })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '할당량 삭제 실패' })
    }
  }

  const handleReset = async (resetType: 'daily' | 'weekly' | 'monthly') => {
    if (!confirm(`정말로 ${resetType} 할당량을 초기화하시겠습니까?`)) {
      return
    }

    try {
      let result
      if (resetType === 'daily') {
        result = await resetDailyQuotas(token)
      } else if (resetType === 'weekly') {
        result = await resetWeeklyQuotas(token)
      } else {
        result = await resetMonthlyQuotas(token)
      }
      setMessage({ type: 'success', text: `${resetType} 할당량 초기화 완료 (${result.reset_count}개)` })
      await loadData()
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '할당량 초기화 실패' })
    }
  }

  return (
    <div className="section-page">
      {/* Header */}
      <div className="section-header">
        <div>
          <h1>📊 업로드 할당량</h1>
          <p className="section-subtitle">플랫폼별 업로드 할당량 관리</p>
        </div>
        <div className="section-actions">
          <button className="btn btn-secondary" onClick={() => void handleReset('daily')}>
            Daily 초기화
          </button>
          <button className="btn btn-secondary" onClick={() => void handleReset('weekly')}>
            Weekly 초기화
          </button>
          <button className="btn btn-secondary" onClick={() => void handleReset('monthly')}>
            Monthly 초기화
          </button>
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

      {/* Create Form */}
      <div className="content-card">
        <h2 className="card-title">
          <span className="card-icon">➕</span>
          새 할당량 생성
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
              <label className="form-label">일일 한도</label>
              <input
                type="number"
                className="form-input"
                value={dailyLimit}
                onChange={(e) => setDailyLimit(e.target.value)}
                min="0"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">주간 한도</label>
              <input
                type="number"
                className="form-input"
                value={weeklyLimit}
                onChange={(e) => setWeeklyLimit(e.target.value)}
                min="0"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">월간 한도</label>
              <input
                type="number"
                className="form-input"
                value={monthlyLimit}
                onChange={(e) => setMonthlyLimit(e.target.value)}
                min="0"
                required
              />
            </div>
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
                할당량 생성
              </>
            )}
          </button>
        </form>
      </div>

      {/* Quota List */}
      <div className="content-card">
        <h2 className="card-title">
          <span className="card-icon">📑</span>
          할당량 목록
        </h2>

        {loading && (
          <div className="empty-state">
            <div className="loading-spinner"></div>
            <p className="empty-state-text">할당량을 불러오는 중...</p>
          </div>
        )}

        {!loading && quotas.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">📊</div>
            <p className="empty-state-text">설정된 할당량이 없습니다.</p>
          </div>
        )}

        {!loading && quotas.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>플랫폼</th>
                <th>Daily (사용/한도)</th>
                <th>Weekly (사용/한도)</th>
                <th>Monthly (사용/한도)</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {quotas.map((quota) => (
                <tr key={quota.id}>
                  <td>#{quota.id}</td>
                  <td>{platforms.find((p) => p.id === quota.platform_id)?.platform_name || '-'}</td>
                  <td>
                    <strong>{quota.used_today}</strong> / {quota.daily_limit}
                  </td>
                  <td>
                    <strong>{quota.used_week}</strong> / {quota.weekly_limit}
                  </td>
                  <td>
                    <strong>{quota.used_month}</strong> / {quota.monthly_limit}
                  </td>
                  <td>
                    <button
                      className="btn btn-danger"
                      onClick={() => void handleDelete(quota.id)}
                    >
                      🗑️ 삭제
                    </button>
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
          할당량 가이드
        </h2>
        <div style={{ fontSize: '0.875rem', color: '#4b5563', lineHeight: '1.6' }}>
          <p><strong>개인 사용 권장:</strong> Daily 2-3, Weekly 10-15, Monthly 30-50</p>
          <p><strong>비즈니스 사용 권장:</strong> Daily 5-7, Weekly 30-40, Monthly 100-150</p>
          <p><strong>초기화 시점:</strong> Daily는 매일 자정, Weekly는 매주 월요일, Monthly는 매달 1일에 자동 초기화됩니다.</p>
          <p><strong>수동 초기화:</strong> 긴급하게 할당량을 늘려야 할 때 사용하세요.</p>
        </div>
      </div>
    </div>
  )
}
