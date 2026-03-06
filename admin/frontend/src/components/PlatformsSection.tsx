import { useState, useEffect } from 'react'
import {
  fetchPlatforms,
  fetchCredentials,
  fetchUploadQuotas,
  createCredential,
  createUploadQuota,
  updateUploadQuota,
  deleteUploadQuota,
  resetDailyQuotas,
  resetWeeklyQuotas,
  resetMonthlyQuotas,
  startYoutubeOAuth,
  completeYoutubeOAuth,
  type PlatformItem,
  type CredentialItem,
  type UploadQuotaItem,
} from '../services/api'
import './SectionStyles.css'

type MessageType = { type: 'success' | 'error'; text: string }

interface Props {
  username: string
  token: string
}

type PlatformWithDetails = {
  platform: PlatformItem
  credentials: CredentialItem[]
  quota: UploadQuotaItem | null
}

export default function PlatformsSection({ username, token }: Props) {
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<MessageType | null>(null)
  const [platformsData, setPlatformsData] = useState<PlatformWithDetails[]>([])
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformWithDetails | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)

  // 인증 정보 폼 상태
  const [credentialName, setCredentialName] = useState('')
  const [credentialJson, setCredentialJson] = useState('{"api_key":""}')
  const [credentialLoading, setCredentialLoading] = useState(false)

  // OAuth 상태
  const [oauthCode, setOauthCode] = useState('')
  const [oauthState, setOauthState] = useState('')
  const [oauthLoading, setOauthLoading] = useState(false)

  // 할당량 폼 상태
  const [quotaDailyLimit, setQuotaDailyLimit] = useState(10)
  const [quotaWeeklyLimit, setQuotaWeeklyLimit] = useState(50)
  const [quotaMonthlyLimit, setQuotaMonthlyLimit] = useState(200)
  const [quotaLoading, setQuotaLoading] = useState(false)

  useEffect(() => {
    void loadData()
  }, [token])

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [message])

  const loadData = async () => {
    try {
      setLoading(true)
      const [platforms, credentials, quotas] = await Promise.all([
        fetchPlatforms(),
        fetchCredentials(token),
        fetchUploadQuotas(token),
      ])

      const combined: PlatformWithDetails[] = platforms.map((platform) => ({
        platform,
        credentials: credentials.filter((c) => c.platform_id === platform.id),
        quota: quotas.find((q) => q.platform_id === platform.id) || null,
      }))

      setPlatformsData(combined)
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handlePlatformClick = (platformData: PlatformWithDetails) => {
    setSelectedPlatform(platformData)
    setShowDetailModal(true)
    
    // 폼 초기화
    if (platformData.quota) {
      setQuotaDailyLimit(platformData.quota.daily_limit)
      setQuotaWeeklyLimit(platformData.quota.weekly_limit)
      setQuotaMonthlyLimit(platformData.quota.monthly_limit)
    } else {
      setQuotaDailyLimit(10)
      setQuotaWeeklyLimit(50)
      setQuotaMonthlyLimit(200)
    }
  }

  const handleCloseModal = () => {
    setShowDetailModal(false)
    setSelectedPlatform(null)
    setCredentialName('')
    setCredentialJson('{"api_key":""}')
    setOauthCode('')
    setOauthState('')
  }

  // 인증 정보 생성
  const handleCreateCredential = async () => {
    if (!selectedPlatform) return

    try {
      setCredentialLoading(true)
      const credentialsObj = JSON.parse(credentialJson)
      await createCredential(token, {
        platform_id: selectedPlatform.platform.id,
        credential_name: credentialName || undefined,
        credentials: credentialsObj,
        is_default: true,
      })
      setMessage({ type: 'success', text: '인증 정보가 생성되었습니다' })
      await loadData()
      setCredentialName('')
      setCredentialJson('{"api_key":""}')
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setCredentialLoading(false)
    }
  }

  // YouTube OAuth 시작
  const handleStartYoutubeOAuth = async () => {
    if (!selectedPlatform) return

    try {
      setOauthLoading(true)
      // Backend의 OAuth 콜백 URI 사용 (Google Cloud Console에 등록된 URI)
      const redirectUri = 'http://localhost:8001/api/v1/oauth/youtube/callback'
      const response = await startYoutubeOAuth(token, selectedPlatform.platform.id, redirectUri)
      setMessage({ type: 'success', text: 'OAuth 창이 열렸습니다. 로그인 후 Code와 State를 복사해주세요.' })
      window.open(response.authorization_url, '_blank', 'width=600,height=700')
      setOauthState(response.state)
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setOauthLoading(false)
    }
  }

  // YouTube OAuth 완료
  const handleCompleteYoutubeOAuth = async () => {
    if (!oauthCode || !oauthState) {
      setMessage({ type: 'error', text: 'OAuth Code와 State를 입력하세요' })
      return
    }

    if (!selectedPlatform) return

    try {
      setOauthLoading(true)
      await completeYoutubeOAuth(oauthCode, oauthState, selectedPlatform.platform.id)
      setMessage({ type: 'success', text: 'YouTube OAuth 인증이 완료되었습니다' })
      await loadData()
      setOauthCode('')
      setOauthState('')
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setOauthLoading(false)
    }
  }

  // 할당량 생성/수정
  const handleSaveQuota = async () => {
    if (!selectedPlatform) return

    try {
      setQuotaLoading(true)
      if (selectedPlatform.quota) {
        // 수정
        await updateUploadQuota(token, selectedPlatform.quota.id, {
          daily_limit: quotaDailyLimit,
          weekly_limit: quotaWeeklyLimit,
          monthly_limit: quotaMonthlyLimit,
        })
        setMessage({ type: 'success', text: '할당량이 수정되었습니다' })
      } else {
        // 생성
        await createUploadQuota(token, {
          platform_id: selectedPlatform.platform.id,
          daily_limit: quotaDailyLimit,
          weekly_limit: quotaWeeklyLimit,
          monthly_limit: quotaMonthlyLimit,
        })
        setMessage({ type: 'success', text: '할당량이 생성되었습니다' })
      }
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setQuotaLoading(false)
    }
  }

  // 할당량 삭제
  const handleDeleteQuota = async () => {
    if (!selectedPlatform?.quota) return

    if (!confirm('정말로 이 할당량을 삭제하시겠습니까?')) return

    try {
      setQuotaLoading(true)
      await deleteUploadQuota(token, selectedPlatform.quota.id)
      setMessage({ type: 'success', text: '할당량이 삭제되었습니다' })
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setQuotaLoading(false)
    }
  }

  // 할당량 리셋
  const handleResetQuota = async (type: 'daily' | 'weekly' | 'monthly') => {
    if (!selectedPlatform?.quota) return

    if (!confirm(`정말로 ${type} 할당량을 초기화하시겠습니까?`)) return

    try {
      setQuotaLoading(true)
      if (type === 'daily') {
        await resetDailyQuotas(token)
      } else if (type === 'weekly') {
        await resetWeeklyQuotas(token)
      } else {
        await resetMonthlyQuotas(token)
      }
      setMessage({ type: 'success', text: `${type} 할당량이 초기화되었습니다` })
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setQuotaLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="content-card">
        <div className="loading-spinner"></div>
        <p>로딩 중...</p>
      </div>
    )
  }

  return (
    <div className="section-container">
      <h2>🌐 플랫폼 관리</h2>
      <p className="section-description">
        플랫폼별 인증 정보, 업로드 할당량, 제한 사항을 통합 관리합니다. (사용자: {username})
      </p>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 플랫폼 카드 그리드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
        {platformsData.map((data) => (
          <div
            key={data.platform.id}
            className="content-card platform-card"
            onClick={() => handlePlatformClick(data)}
            style={{
              cursor: 'pointer',
              transition: 'all 0.2s',
              border: '2px solid #e5e7eb',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)'
              e.currentTarget.style.transform = 'translateY(-2px)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = ''
              e.currentTarget.style.transform = ''
            }}
          >
            {/* 헤더 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
              <div style={{ fontSize: '3rem' }}>
                {data.platform.platform_code === 'youtube' ? '📺' :
                  data.platform.platform_code === 'tiktok' ? '🎵' :
                    data.platform.platform_code === 'instagram' ? '📷' :
                      data.platform.platform_code === 'facebook' ? '👥' : '📱'}
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: 0, fontSize: '1.3rem', color: '#1f2937' }}>
                  {data.platform.platform_name}
                </h3>
                <p style={{ margin: '0.25rem 0 0 0', color: '#6b7280', fontSize: '0.85rem' }}>
                  {data.platform.platform_code}
                </p>
              </div>
            </div>

            {/* 상태 정보 */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '0.5rem' }}>
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>인증 정보</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: data.credentials.length > 0 ? '#10b981' : '#ef4444' }}>
                  {data.credentials.length > 0 ? `${data.credentials.length}개` : '미등록'}
                </div>
              </div>
              <div style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '0.5rem' }}>
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>업로드 할당량</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: data.quota ? '#10b981' : '#ef4444' }}>
                  {data.quota ? '설정됨' : '미설정'}
                </div>
              </div>
            </div>

            {/* 할당량 사용 현황 */}
            {data.quota && (
              <div style={{ padding: '0.75rem', background: '#eff6ff', borderRadius: '0.5rem', border: '1px solid #bfdbfe' }}>
                <div style={{ fontSize: '0.75rem', color: '#1e40af', marginBottom: '0.5rem', fontWeight: 600 }}>
                  📊 오늘 사용량
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#1e3a8a' }}>
                  <span>일일: {data.quota.used_today}/{data.quota.daily_limit}</span>
                  <span>주간: {data.quota.used_week}/{data.quota.weekly_limit}</span>
                  <span>월간: {data.quota.used_month}/{data.quota.monthly_limit}</span>
                </div>
                {data.quota.is_quota_exceeded && (
                  <div style={{ marginTop: '0.5rem', color: '#dc2626', fontSize: '0.75rem', fontWeight: 600 }}>
                    ⚠️ 할당량 초과
                  </div>
                )}
              </div>
            )}

            {/* 제한 사항 */}
            {data.platform.constraints && (
              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem' }}>제한 사항</div>
                <div style={{ fontSize: '0.8rem', color: '#4b5563', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {data.platform.constraints.max_duration_seconds && (
                    <div>⏱️ 최대 길이: {data.platform.constraints.max_duration_seconds}초</div>
                  )}
                  {data.platform.constraints.max_video_size_mb && (
                    <div>📦 최대 용량: {data.platform.constraints.max_video_size_mb}MB</div>
                  )}
                  {data.platform.constraints.daily_limit && (
                    <div>📅 일일 제한: {data.platform.constraints.daily_limit}개</div>
                  )}
                </div>
              </div>
            )}

            <div style={{ marginTop: '1rem', textAlign: 'right' }}>
              <button
                className="btn-primary"
                style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                onClick={(e) => {
                  e.stopPropagation()
                  handlePlatformClick(data)
                }}
              >
                상세 설정 →
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 상세 설정 모달 */}
      {showDetailModal && selectedPlatform && (
        <div
          className="modal-overlay"
          onClick={handleCloseModal}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'white',
              borderRadius: '0.75rem',
              padding: '2rem',
              maxWidth: '900px',
              width: '90%',
              maxHeight: '90vh',
              overflow: 'auto',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            }}
          >
            {/* 모달 헤더 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ fontSize: '3rem' }}>
                  {selectedPlatform.platform.platform_code === 'youtube' ? '📺' :
                    selectedPlatform.platform.platform_code === 'tiktok' ? '🎵' :
                      selectedPlatform.platform.platform_code === 'instagram' ? '📷' :
                        selectedPlatform.platform.platform_code === 'facebook' ? '👥' : '📱'}
                </div>
                <div>
                  <h2 style={{ margin: 0, fontSize: '1.8rem', color: '#1f2937' }}>
                    {selectedPlatform.platform.platform_name}
                  </h2>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#6b7280', fontSize: '0.9rem' }}>
                    {selectedPlatform.platform.platform_code} (ID: {selectedPlatform.platform.id})
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseModal}
                style={{
                  background: 'transparent',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#6b7280',
                }}
              >
                ✕
              </button>
            </div>

            {/* 탭 컨테이너 */}
            <div>
              {/* 1. 인증 정보 섹션 */}
              <div className="content-card" style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  🔐 인증 정보
                  <span style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 'normal' }}>
                    ({selectedPlatform.credentials.length}개 등록됨)
                  </span>
                </h3>

                {/* 기존 인증 정보 목록 */}
                {selectedPlatform.credentials.length > 0 && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <table className="data-table" style={{ fontSize: '0.85rem' }}>
                      <thead>
                        <tr>
                          <th>이름</th>
                          <th>상태</th>
                          <th>기본값</th>
                          <th>생성일</th>
                          <th>마지막 검증</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedPlatform.credentials.map((cred) => (
                          <tr key={cred.id}>
                            <td>{cred.credential_name || `Credential #${cred.id}`}</td>
                            <td>
                              <span className={`status-badge ${cred.status === 'active' ? 'online' : 'offline'}`}>
                                {cred.status}
                              </span>
                            </td>
                            <td>{cred.is_default ? '✅' : '-'}</td>
                            <td>{new Date(cred.created_at).toLocaleDateString()}</td>
                            <td>{cred.last_validated ? new Date(cred.last_validated).toLocaleDateString() : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* YouTube OAuth */}
                {selectedPlatform.platform.platform_code === 'youtube' && (
                  <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '0.5rem', marginBottom: '1rem' }}>
                    <h4 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>YouTube OAuth 인증</h4>
                    <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
                      <button
                        className="btn-primary"
                        onClick={handleStartYoutubeOAuth}
                        disabled={oauthLoading}
                        style={{ fontSize: '0.85rem' }}
                      >
                        {oauthLoading ? '처리 중...' : '1. OAuth 시작'}
                      </button>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                      <input
                        type="text"
                        placeholder="OAuth Code"
                        value={oauthCode}
                        onChange={(e) => setOauthCode(e.target.value)}
                        style={{ padding: '0.5rem', fontSize: '0.85rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      />
                      <input
                        type="text"
                        placeholder="State"
                        value={oauthState}
                        onChange={(e) => setOauthState(e.target.value)}
                        style={{ padding: '0.5rem', fontSize: '0.85rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      />
                    </div>
                    <button
                      className="btn-primary"
                      onClick={handleCompleteYoutubeOAuth}
                      disabled={oauthLoading}
                      style={{ fontSize: '0.85rem', marginTop: '0.75rem', width: '100%' }}
                    >
                      {oauthLoading ? '처리 중...' : '2. OAuth 완료'}
                    </button>
                  </div>
                )}

                {/* 일반 인증 정보 추가 */}
                <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '0.5rem' }}>
                  <h4 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>새 인증 정보 추가</h4>
                  <div style={{ marginBottom: '0.75rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>
                      이름 (선택)
                    </label>
                    <input
                      type="text"
                      placeholder="예: 내 계정 1"
                      value={credentialName}
                      onChange={(e) => setCredentialName(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', fontSize: '0.85rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                    />
                  </div>
                  <div style={{ marginBottom: '0.75rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>
                      인증 데이터 (JSON)
                    </label>
                    <textarea
                      placeholder='{"api_key": "YOUR_API_KEY"}'
                      value={credentialJson}
                      onChange={(e) => setCredentialJson(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        fontSize: '0.85rem',
                        fontFamily: 'monospace',
                        border: '1px solid #d1d5db',
                        borderRadius: '0.375rem',
                        minHeight: '100px',
                      }}
                    />
                  </div>
                  <button
                    className="btn-primary"
                    onClick={handleCreateCredential}
                    disabled={credentialLoading}
                    style={{ fontSize: '0.85rem', width: '100%' }}
                  >
                    {credentialLoading ? '생성 중...' : '인증 정보 생성'}
                  </button>
                </div>
              </div>

              {/* 2. 업로드 할당량 섹션 */}
              <div className="content-card" style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  📊 업로드 할당량
                  {selectedPlatform.quota && (
                    <span style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: 'normal' }}>
                      (설정됨)
                    </span>
                  )}
                </h3>

                {/* 현재 사용 현황 */}
                {selectedPlatform.quota && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                      <div style={{ padding: '1rem', background: '#eff6ff', borderRadius: '0.5rem', border: '1px solid #bfdbfe' }}>
                        <div style={{ fontSize: '0.75rem', color: '#1e40af', marginBottom: '0.5rem', fontWeight: 600 }}>
                          일일 (Daily)
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e3a8a', marginBottom: '0.25rem' }}>
                          {selectedPlatform.quota.used_today}/{selectedPlatform.quota.daily_limit}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#1e40af' }}>
                          남은 개수: {selectedPlatform.quota.remaining_daily}
                        </div>
                        <button
                          className="btn-secondary"
                          onClick={() => handleResetQuota('daily')}
                          disabled={quotaLoading}
                          style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem', marginTop: '0.5rem', width: '100%' }}
                        >
                          초기화
                        </button>
                      </div>
                      <div style={{ padding: '1rem', background: '#f0fdf4', borderRadius: '0.5rem', border: '1px solid #bbf7d0' }}>
                        <div style={{ fontSize: '0.75rem', color: '#15803d', marginBottom: '0.5rem', fontWeight: 600 }}>
                          주간 (Weekly)
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#166534', marginBottom: '0.25rem' }}>
                          {selectedPlatform.quota.used_week}/{selectedPlatform.quota.weekly_limit}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#15803d' }}>
                          남은 개수: {selectedPlatform.quota.remaining_weekly}
                        </div>
                        <button
                          className="btn-secondary"
                          onClick={() => handleResetQuota('weekly')}
                          disabled={quotaLoading}
                          style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem', marginTop: '0.5rem', width: '100%' }}
                        >
                          초기화
                        </button>
                      </div>
                      <div style={{ padding: '1rem', background: '#fef3c7', borderRadius: '0.5rem', border: '1px solid #fde68a' }}>
                        <div style={{ fontSize: '0.75rem', color: '#92400e', marginBottom: '0.5rem', fontWeight: 600 }}>
                          월간 (Monthly)
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#78350f', marginBottom: '0.25rem' }}>
                          {selectedPlatform.quota.used_month}/{selectedPlatform.quota.monthly_limit}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#92400e' }}>
                          남은 개수: {selectedPlatform.quota.remaining_monthly}
                        </div>
                        <button
                          className="btn-secondary"
                          onClick={() => handleResetQuota('monthly')}
                          disabled={quotaLoading}
                          style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem', marginTop: '0.5rem', width: '100%' }}
                        >
                          초기화
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 할당량 설정 폼 */}
                <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '0.5rem' }}>
                  <h4 style={{ margin: '0 0 1rem 0', fontSize: '1rem' }}>
                    {selectedPlatform.quota ? '할당량 수정' : '할당량 설정'}
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>
                        일일 제한
                      </label>
                      <input
                        type="number"
                        value={quotaDailyLimit}
                        onChange={(e) => setQuotaDailyLimit(parseInt(e.target.value) || 0)}
                        style={{ width: '100%', padding: '0.5rem', fontSize: '0.85rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>
                        주간 제한
                      </label>
                      <input
                        type="number"
                        value={quotaWeeklyLimit}
                        onChange={(e) => setQuotaWeeklyLimit(parseInt(e.target.value) || 0)}
                        style={{ width: '100%', padding: '0.5rem', fontSize: '0.85rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>
                        월간 제한
                      </label>
                      <input
                        type="number"
                        value={quotaMonthlyLimit}
                        onChange={(e) => setQuotaMonthlyLimit(parseInt(e.target.value) || 0)}
                        style={{ width: '100%', padding: '0.5rem', fontSize: '0.85rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button
                      className="btn-primary"
                      onClick={handleSaveQuota}
                      disabled={quotaLoading}
                      style={{ fontSize: '0.85rem', flex: 1 }}
                    >
                      {quotaLoading ? '처리 중...' : selectedPlatform.quota ? '수정' : '생성'}
                    </button>
                    {selectedPlatform.quota && (
                      <button
                        className="btn-danger"
                        onClick={handleDeleteQuota}
                        disabled={quotaLoading}
                        style={{ fontSize: '0.85rem' }}
                      >
                        삭제
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* 3. 플랫폼 제한 사항 */}
              <div className="content-card">
                <h3 style={{ marginBottom: '1rem' }}>⚙️ 플랫폼 제한 사항</h3>
                <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '0.5rem' }}>
                  {selectedPlatform.platform.constraints ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                      {selectedPlatform.platform.constraints.hourly_limit && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>시간당 제한</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedPlatform.platform.constraints.hourly_limit}개</div>
                        </div>
                      )}
                      {selectedPlatform.platform.constraints.daily_limit && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>일일 제한</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedPlatform.platform.constraints.daily_limit}개</div>
                        </div>
                      )}
                      {selectedPlatform.platform.constraints.max_duration_seconds && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>최대 영상 길이</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedPlatform.platform.constraints.max_duration_seconds}초</div>
                        </div>
                      )}
                      {selectedPlatform.platform.constraints.max_video_size_mb && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>최대 파일 크기</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedPlatform.platform.constraints.max_video_size_mb}MB</div>
                        </div>
                      )}
                      {selectedPlatform.platform.constraints.supported_resolutions && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>지원 해상도</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                            {selectedPlatform.platform.constraints.supported_resolutions.join(', ')}
                          </div>
                        </div>
                      )}
                      {selectedPlatform.platform.constraints.supported_formats && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>지원 포맷</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                            {selectedPlatform.platform.constraints.supported_formats.join(', ')}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>제한 사항 정보가 없습니다.</p>
                  )}
                </div>
              </div>
            </div>

            {/* 모달 푸터 */}
            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                className="btn-secondary"
                onClick={handleCloseModal}
                style={{ fontSize: '0.9rem' }}
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 안내 */}
      <div className="content-card" style={{ marginTop: '1.5rem', background: '#f8f9fa' }}>
        <h3>💡 플랫폼 통합 관리 가이드</h3>
        <ul style={{ lineHeight: '1.8', fontSize: '0.9rem' }}>
          <li><strong>플랫폼 카드:</strong> 각 플랫폼의 인증 상태, 할당량 사용 현황을 한눈에 확인할 수 있습니다.</li>
          <li><strong>상세 설정:</strong> 플랫폼 카드를 클릭하면 인증 정보, 할당량, 제한 사항을 통합 관리할 수 있습니다.</li>
          <li><strong>인증 정보:</strong> YouTube는 OAuth, TikTok은 쿠키 기반 인증을 지원합니다.</li>
          <li><strong>할당량 관리:</strong> 일일/주간/월간 업로드 제한을 설정하고, 실시간으로 사용 현황을 모니터링합니다.</li>
          <li><strong>자동 리셋:</strong> 할당량은 설정된 주기에 따라 자동으로 초기화되며, 수동으로도 초기화할 수 있습니다.</li>
        </ul>
      </div>
    </div>
  )
}
