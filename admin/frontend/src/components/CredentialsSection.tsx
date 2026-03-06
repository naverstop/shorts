import { useState, useEffect } from 'react'
import {
  fetchCredentials,
  fetchPlatforms,
  startYoutubeOAuth,
  type CredentialItem,
  type PlatformItem,
} from '../services/api'
import './SectionStyles.css'

type MessageType = { type: 'success' | 'error'; text: string }

interface Props {
  token: string
  username: string
}

export default function CredentialsSection({ token, username }: Props) {
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<MessageType | null>(null)
  const [credentials, setCredentials] = useState<CredentialItem[]>([])
  const [platforms, setPlatforms] = useState<PlatformItem[]>([])

  // 선택된 플랫폼
  const [selectedPlatform, setSelectedPlatform] = useState<number>(0)

  useEffect(() => {
    void loadData()
  }, [])

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [message])

  const loadData = async () => {
    try {
      setLoading(true)
      const [credentialsData, platformsData] = await Promise.all([
        fetchCredentials(token),
        fetchPlatforms(),
      ])
      setCredentials(credentialsData)
      setPlatforms(platformsData)
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handleStartYoutubeOAuth = async () => {
    if (!selectedPlatform) {
      setMessage({ type: 'error', text: '플랫폼을 선택해주세요.' })
      return
    }

    try {
      const redirectUri = `${window.location.origin}/oauth/youtube/callback`
      const result = await startYoutubeOAuth(token, selectedPlatform, redirectUri)
      
      // OAuth 페이지로 리다이렉트
      window.location.href = result.authorization_url
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    }
  }

  const handleManualCredential = () => {
    setMessage({ 
      type: 'success', 
      text: 'TikTok 쿠키 수동 입력 기능은 곧 지원될 예정입니다.' 
    })
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
      <h2>🔐 인증정보 관리</h2>
      <p className="section-description">
        플랫폼 연동을 위한 인증 정보를 관리합니다. (사용자: {username})
      </p>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* OAuth 연동 */}
      <div className="content-card">
        <h3>✨ 새 인증 정보 추가</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>플랫폼</label>
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(Number(e.target.value))}
            >
              <option value={0}>-- 플랫폼 선택 --</option>
              {platforms.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.platform_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          <button
            className="btn btn-primary"
            onClick={() => void handleStartYoutubeOAuth()}
            disabled={!selectedPlatform}
          >
            🔗 YouTube OAuth 연동
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleManualCredential}
          >
            📝 TikTok 쿠키 수동 입력
          </button>
        </div>
      </div>

      {/* 인증 정보 목록 */}
      <div className="content-card">
        <h3>📋 등록된 인증 정보</h3>
        {credentials.length === 0 ? (
          <p className="empty-state">등록된 인증 정보가 없습니다.</p>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>플랫폼</th>
                  <th>이름</th>
                  <th>상태</th>
                  <th>기본값</th>
                  <th>Access Token</th>
                  <th>Refresh Token</th>
                  <th>마지막 검증</th>
                  <th>생성일</th>
                </tr>
              </thead>
              <tbody>
                {credentials.map((cred) => (
                  <tr key={cred.id}>
                    <td>{cred.id}</td>
                    <td>
                      {platforms.find((p) => p.id === cred.platform_id)?.platform_name || '-'}
                    </td>
                    <td>{cred.credential_name || '(이름 없음)'}</td>
                    <td>
                      <span className={`status-badge ${cred.status === 'active' ? 'online' : 'offline'}`}>
                        {cred.status}
                      </span>
                    </td>
                    <td>{cred.is_default ? '⭐' : '-'}</td>
                    <td>{cred.has_access_token ? '✅' : '❌'}</td>
                    <td>{cred.has_refresh_token ? '✅' : '❌'}</td>
                    <td>{cred.last_validated ? new Date(cred.last_validated).toLocaleString('ko-KR') : '-'}</td>
                    <td>{new Date(cred.created_at).toLocaleString('ko-KR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 사용 가이드 */}
      <div className="content-card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <h3>💡 사용 가이드</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li><strong>YouTube OAuth:</strong> Google 계정으로 로그인하여 자동으로 인증 정보를 생성합니다.</li>
          <li><strong>TikTok 쿠키:</strong> 브라우저 개발자 도구에서 쿠키를 추출하여 수동으로 입력합니다.</li>
          <li><strong>기본값 설정:</strong> 여러 인증 정보 중 기본으로 사용할 것을 선택합니다.</li>
          <li><strong>상태 확인:</strong> Active 상태만 실제 게시에 사용됩니다.</li>
        </ul>
      </div>
    </div>
  )
}
