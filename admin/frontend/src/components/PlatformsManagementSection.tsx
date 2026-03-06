import { useState, useEffect } from 'react'
import {
  fetchPlatforms,
  createPlatform,
  updatePlatform,
  deletePlatform,
  type PlatformItem,
} from '../services/api'
import './SectionStyles.css'

interface Props {
  token: string
}

export default function PlatformsManagementSection({ token }: Props) {
  const [loading, setLoading] = useState(true)
  const [platforms, setPlatforms] = useState<PlatformItem[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformItem | null>(null)

  // 폼 상태
  const [platformCode, setPlatformCode] = useState('')
  const [platformName, setPlatformName] = useState('')
  const [authType, setAuthType] = useState('oauth2')
  const [isActive, setIsActive] = useState(true)
  const [apiEndpoint, setApiEndpoint] = useState('')
  const [documentationUrl, setDocumentationUrl] = useState('')

  // 정렬 상태
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    void loadPlatforms()
  }, [])

  const loadPlatforms = async () => {
    try {
      setLoading(true)
      const data = await fetchPlatforms()
      setPlatforms(data)
    } catch (err) {
      alert(`플랫폼 목록 로드 실패: ${(err as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const getSortedPlatforms = () => {
    if (!sortColumn) return platforms

    return [...platforms].sort((a, b) => {
      let aVal: any = a[sortColumn as keyof PlatformItem]
      let bVal: any = b[sortColumn as keyof PlatformItem]

      if (aVal === null || aVal === undefined) aVal = ''
      if (bVal === null || bVal === undefined) bVal = ''

      if (typeof aVal === 'string') aVal = aVal.toLowerCase()
      if (typeof bVal === 'string') bVal = bVal.toLowerCase()

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
  }

  const resetForm = () => {
    setPlatformCode('')
    setPlatformName('')
    setAuthType('oauth2')
    setIsActive(true)
    setApiEndpoint('')
    setDocumentationUrl('')
  }

  const handleCreateClick = () => {
    resetForm()
    setShowCreateModal(true)
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!platformCode.trim() || !platformName.trim()) {
      alert('플랫폼 코드와 이름은 필수입니다.')
      return
    }

    try {
      await createPlatform(token, {
        platform_code: platformCode.trim(),
        platform_name: platformName.trim(),
        auth_type: authType,
        api_endpoint: apiEndpoint.trim() || undefined,
        documentation_url: documentationUrl.trim() || undefined,
      })
      alert('플랫폼이 생성되었습니다.')
      setShowCreateModal(false)
      await loadPlatforms()
    } catch (err) {
      alert(`생성 실패: ${(err as Error).message}`)
    }
  }

  const handleEditClick = (platform: PlatformItem) => {
    setSelectedPlatform(platform)
    setPlatformCode(platform.platform_code)
    setPlatformName(platform.platform_name)
    setAuthType(platform.auth_type || 'oauth2')
    setIsActive(platform.is_active ?? true)
    setApiEndpoint(platform.api_endpoint || '')
    setDocumentationUrl(platform.documentation_url || '')
    setShowEditModal(true)
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedPlatform) return

    if (!platformName.trim()) {
      alert('플랫폼 이름은 필수입니다.')
      return
    }

    try {
      await updatePlatform(token, selectedPlatform.id, {
        platform_name: platformName.trim(),
        auth_type: authType,
        is_active: isActive,
        api_endpoint: apiEndpoint.trim() || undefined,
        documentation_url: documentationUrl.trim() || undefined,
      })
      alert('플랫폼이 수정되었습니다.')
      setShowEditModal(false)
      await loadPlatforms()
    } catch (err) {
      alert(`수정 실패: ${(err as Error).message}`)
    }
  }

  const handleDelete = async (platform: PlatformItem) => {
    if (!window.confirm(`'${platform.platform_name}' 플랫폼을 삭제하시겠습니까?`)) {
      return
    }

    try {
      await deletePlatform(token, platform.id)
      alert('플랫폼이 삭제되었습니다.')
      await loadPlatforms()
    } catch (err) {
      alert(`삭제 실패: ${(err as Error).message}`)
    }
  }

  const handleDetailClick = (platform: PlatformItem) => {
    setSelectedPlatform(platform)
    setShowDetailModal(true)
  }

  const getStatusBadge = (isActive: boolean | undefined) => {
    if (isActive === false) {
      return <span className="badge badge-danger">비활성</span>
    }
    return <span className="badge badge-success">활성</span>
  }

  const getAuthTypeBadge = (authType: string | undefined) => {
    const type = authType || 'unknown'
    const colors: Record<string, string> = {
      oauth2: 'primary',
      api_key: 'info',
      credentials: 'warning',
    }
    const color = colors[type] || 'secondary'
    return <span className={`badge badge-${color}`}>{type.toUpperCase()}</span>
  }

  const sortIcon = (column: string) => {
    if (sortColumn !== column) return null
    return sortDirection === 'asc' ? ' ▲' : ' ▼'
  }

  if (loading) {
    return <div className="loading">플랫폼 목록을 불러오는 중...</div>
  }

  return (
    <div className="section-content">
      <div className="section-header">
        <div>
          <h2>🌐 플랫폼 관리</h2>
          <p className="section-subtitle">
            YouTube, TikTok 등 등록된 플랫폼을 관리합니다. (총 {platforms.length}개)
          </p>
        </div>
        <button className="btn btn-primary" onClick={handleCreateClick}>
          + 플랫폼 생성
        </button>
      </div>

      {platforms.length === 0 ? (
        <div className="empty-state">
          <p>등록된 플랫폼이 없습니다.</p>
          <p className="text-muted">상단의 '플랫폼 생성' 버튼을 눌러 새 플랫폼을 추가하세요.</p>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '60px' }}>순번</th>
              <th onClick={() => handleSort('platform_code')} style={{ cursor: 'pointer' }}>
                플랫폼 코드{sortIcon('platform_code')}
              </th>
              <th onClick={() => handleSort('platform_name')} style={{ cursor: 'pointer' }}>
                플랫폼명{sortIcon('platform_name')}
              </th>
              <th onClick={() => handleSort('auth_type')} style={{ cursor: 'pointer' }}>
                인증 타입{sortIcon('auth_type')}
              </th>
              <th onClick={() => handleSort('is_active')} style={{ cursor: 'pointer' }}>
                상태{sortIcon('is_active')}
              </th>
              <th style={{ width: '240px' }}>작업</th>
            </tr>
          </thead>
          <tbody>
            {getSortedPlatforms().map((platform, index) => (
              <tr key={platform.id}>
                <td className="text-center">{index + 1}</td>
                <td>
                  <code>{platform.platform_code}</code>
                </td>
                <td className="text-bold">{platform.platform_name}</td>
                <td>{getAuthTypeBadge(platform.auth_type)}</td>
                <td>{getStatusBadge(platform.is_active)}</td>
                <td>
                  <div className="btn-group">
                    <button
                      className="btn btn-sm btn-info"
                      onClick={() => handleDetailClick(platform)}
                    >
                      상세
                    </button>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleEditClick(platform)}
                    >
                      수정
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDelete(platform)}
                    >
                      삭제
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* 생성 모달 */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ fontSize: '2rem' }}>🚀</div>
                <h3 style={{ margin: 0, fontSize: '1.5rem' }}>플랫폼 생성</h3>
              </div>
              <button className="modal-close" onClick={() => setShowCreateModal(false)} style={{ color: 'white', opacity: 0.9 }}>
                ×
              </button>
            </div>
            <form onSubmit={handleCreateSubmit}>
              <div className="modal-body" style={{ padding: '1.5rem' }}>
                {/* 기본 정보 섹션 */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '1rem', color: '#495057', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>📋</span> 기본 정보
                  </h4>
                  <div style={{ background: '#f8f9fa', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        플랫폼 코드 <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={platformCode}
                        onChange={(e) => setPlatformCode(e.target.value)}
                        placeholder="예: youtube, tiktok, instagram"
                        required
                        maxLength={20}
                        style={{ fontFamily: 'monospace' }}
                      />
                      <small className="form-text" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem' }}>
                        <span>💡</span> 영문 소문자, 숫자, 언더스코어만 사용 가능
                      </small>
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        플랫폼 이름 <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={platformName}
                        onChange={(e) => setPlatformName(e.target.value)}
                        placeholder="예: YouTube, TikTok, Instagram"
                        required
                        maxLength={50}
                      />
                      <small className="form-text" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem' }}>
                        <span>✏️</span> 사용자에게 표시될 이름
                      </small>
                    </div>
                  </div>
                </div>

                {/* 인증 설정 섹션 */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '1rem', color: '#495057', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>🔐</span> 인증 설정
                  </h4>
                  <div style={{ background: '#f8f9fa', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        인증 타입 <span className="text-danger">*</span>
                      </label>
                      <select
                        className="form-control"
                        value={authType}
                        onChange={(e) => setAuthType(e.target.value)}
                        required
                      >
                        <option value="oauth2">🔑 OAuth2</option>
                        <option value="api_key">🗝️ API Key</option>
                        <option value="credentials">🔒 Credentials</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* 추가 설정 섹션 */}
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '1rem', color: '#495057', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>⚙️</span> 추가 설정 (선택)
                  </h4>
                  <div style={{ background: '#f8f9fa', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        🔗 API 엔드포인트
                      </label>
                      <input
                        type="url"
                        className="form-control"
                        value={apiEndpoint}
                        onChange={(e) => setApiEndpoint(e.target.value)}
                        placeholder="https://api.example.com/v1"
                        style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
                      />
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        📚 문서 URL
                      </label>
                      <input
                        type="url"
                        className="form-control"
                        value={documentationUrl}
                        onChange={(e) => setDocumentationUrl(e.target.value)}
                        placeholder="https://docs.example.com"
                        style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="modal-actions" style={{ padding: '1rem 1.5rem', background: '#f8f9fa', borderTop: '1px solid #dee2e6' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                  취소
                </button>
                <button type="submit" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>✨</span> 생성
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 수정 모달 */}
      {showEditModal && selectedPlatform && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white', padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ fontSize: '2rem' }}>✏️</div>
                <h3 style={{ margin: 0, fontSize: '1.5rem' }}>플랫폼 수정</h3>
              </div>
              <button className="modal-close" onClick={() => setShowEditModal(false)} style={{ color: 'white', opacity: 0.9 }}>
                ×
              </button>
            </div>
            <form onSubmit={handleEditSubmit}>
              <div className="modal-body" style={{ padding: '1.5rem' }}>
                {/* 기본 정보 섹션 */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '1rem', color: '#495057', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>📋</span> 기본 정보
                  </h4>
                  <div style={{ background: '#f8f9fa', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label style={{ fontWeight: '600', color: '#6c757d', marginBottom: '0.5rem', display: 'block' }}>
                        플랫폼 코드 (변경 불가)
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={platformCode}
                        disabled
                        style={{ backgroundColor: '#e9ecef', fontFamily: 'monospace', cursor: 'not-allowed' }}
                      />
                      <small className="form-text" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem', color: '#6c757d' }}>
                        <span>🔒</span> 플랫폼 코드는 생성 후 변경할 수 없습니다
                      </small>
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        플랫폼 이름 <span className="text-danger">*</span>
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={platformName}
                        onChange={(e) => setPlatformName(e.target.value)}
                        required
                        maxLength={50}
                      />
                    </div>
                  </div>
                </div>

                {/* 인증 및 상태 설정 섹션 */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '1rem', color: '#495057', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>🔐</span> 인증 및 상태 설정
                  </h4>
                  <div style={{ background: '#f8f9fa', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        인증 타입 <span className="text-danger">*</span>
                      </label>
                      <select
                        className="form-control"
                        value={authType}
                        onChange={(e) => setAuthType(e.target.value)}
                        required
                      >
                        <option value="oauth2">🔑 OAuth2</option>
                        <option value="api_key">🗝️ API Key</option>
                        <option value="credentials">🔒 Credentials</option>
                      </select>
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        padding: '0.75rem', 
                        background: isActive ? '#d1ecf1' : '#f8d7da', 
                        borderRadius: '0.375rem',
                        border: isActive ? '1px solid #bee5eb' : '1px solid #f5c6cb',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}>
                        <input
                          type="checkbox"
                          checked={isActive}
                          onChange={(e) => setIsActive(e.target.checked)}
                          style={{ marginRight: '0.75rem', width: '18px', height: '18px', cursor: 'pointer' }}
                        />
                        <span style={{ fontWeight: '600', color: '#495057' }}>
                          {isActive ? '✅ 활성화' : '❌ 비활성화'}
                        </span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* 추가 설정 섹션 */}
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '1rem', color: '#495057', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>⚙️</span> 추가 설정 (선택)
                  </h4>
                  <div style={{ background: '#f8f9fa', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        🔗 API 엔드포인트
                      </label>
                      <input
                        type="url"
                        className="form-control"
                        value={apiEndpoint}
                        onChange={(e) => setApiEndpoint(e.target.value)}
                        style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
                      />
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontWeight: '600', color: '#495057', marginBottom: '0.5rem', display: 'block' }}>
                        📚 문서 URL
                      </label>
                      <input
                        type="url"
                        className="form-control"
                        value={documentationUrl}
                        onChange={(e) => setDocumentationUrl(e.target.value)}
                        style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="modal-actions" style={{ padding: '1rem 1.5rem', background: '#f8f9fa', borderTop: '1px solid #dee2e6' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowEditModal(false)}>
                  취소
                </button>
                <button type="submit" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>💾</span> 수정
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 상세 모달 */}
      {showDetailModal && selectedPlatform && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ fontSize: '2.5rem' }}>
                  {selectedPlatform.platform_code === 'youtube' && '📺'}
                  {selectedPlatform.platform_code === 'tiktok' && '🎵'}
                  {selectedPlatform.platform_code === 'instagram' && '📸'}
                  {selectedPlatform.platform_code === 'facebook' && '👥'}
                  {!['youtube', 'tiktok', 'instagram', 'facebook'].includes(selectedPlatform.platform_code) && '🌐'}
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.5rem' }}>{selectedPlatform.platform_name}</h3>
                  <div style={{ fontSize: '0.9rem', opacity: 0.9, marginTop: '0.25rem' }}>
                    <code style={{ background: 'rgba(255,255,255,0.2)', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                      {selectedPlatform.platform_code}
                    </code>
                  </div>
                </div>
              </div>
              <button className="modal-close" onClick={() => setShowDetailModal(false)} style={{ color: 'white', opacity: 0.9 }}>
                ×
              </button>
            </div>
            
            <div className="modal-body" style={{ padding: '1.5rem' }}>
              {/* 상태 및 인증 정보 */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                  <div style={{ fontSize: '0.85rem', color: '#6c757d', marginBottom: '0.5rem', fontWeight: 'bold' }}>상태</div>
                  <div>{getStatusBadge(selectedPlatform.is_active)}</div>
                </div>
                <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '0.5rem', border: '1px solid #dee2e6' }}>
                  <div style={{ fontSize: '0.85rem', color: '#6c757d', marginBottom: '0.5rem', fontWeight: 'bold' }}>인증 타입</div>
                  <div>{getAuthTypeBadge(selectedPlatform.auth_type)}</div>
                </div>
              </div>

              {/* API 엔드포인트 */}
              {selectedPlatform.api_endpoint && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#495057' }}>
                    🔗 API 엔드포인트
                  </div>
                  <div style={{ 
                    background: '#e9ecef', 
                    padding: '0.75rem', 
                    borderRadius: '0.375rem', 
                    fontFamily: 'monospace', 
                    fontSize: '0.85rem',
                    wordBreak: 'break-all',
                    border: '1px solid #dee2e6'
                  }}>
                    <a 
                      href={selectedPlatform.api_endpoint} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ color: '#0066cc', textDecoration: 'none' }}
                    >
                      {selectedPlatform.api_endpoint}
                    </a>
                  </div>
                </div>
              )}

              {/* 문서 URL */}
              {selectedPlatform.documentation_url && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#495057' }}>
                    📚 개발 문서
                  </div>
                  <div style={{ 
                    background: '#e9ecef', 
                    padding: '0.75rem', 
                    borderRadius: '0.375rem', 
                    fontFamily: 'monospace', 
                    fontSize: '0.85rem',
                    wordBreak: 'break-all',
                    border: '1px solid #dee2e6'
                  }}>
                    <a 
                      href={selectedPlatform.documentation_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ color: '#0066cc', textDecoration: 'none' }}
                    >
                      {selectedPlatform.documentation_url}
                    </a>
                  </div>
                </div>
              )}

              {/* 필수 필드 */}
              {selectedPlatform.required_fields && Object.keys(selectedPlatform.required_fields).length > 0 && (
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '0.75rem', color: '#495057' }}>
                    ⚙️ 필수 인증 필드
                  </div>
                  <div style={{ 
                    background: '#f8f9fa', 
                    padding: '1rem', 
                    borderRadius: '0.5rem',
                    border: '1px solid #dee2e6'
                  }}>
                    {Object.entries(selectedPlatform.required_fields).map(([key, value]) => (
                      <div key={key} style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        padding: '0.5rem 0',
                        borderBottom: '1px solid #dee2e6'
                      }}>
                        <span style={{ fontWeight: '500', color: '#495057' }}>{key}</span>
                        <code style={{ 
                          background: '#e9ecef', 
                          padding: '0.25rem 0.5rem', 
                          borderRadius: '0.25rem',
                          fontSize: '0.85rem'
                        }}>
                          {String(value)}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="modal-actions" style={{ padding: '1rem 1.5rem', background: '#f8f9fa', borderTop: '1px solid #dee2e6' }}>
              <button className="btn btn-secondary" onClick={() => setShowDetailModal(false)}>
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
