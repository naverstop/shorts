import { useEffect, useState } from 'react'
import './SectionStyles.css'
import {
  fetchSimCards,
  fetchSimCardDetail,
  createSimCard,
  updateSimCard,
  deleteSimCard,
  fetchPlatforms,
  createPlatformAccount,
  updatePlatformAccount,
  deletePlatformAccount,
  validatePlatformCredentials,
  type SimCardItem,
  type SimCardDetailItem,
  type SimCardCreateRequest,
  type SimCardUpdateRequest,
  type PlatformItem,
  type PlatformAccountCreateRequest,
  type PlatformAccountUpdateRequest,
} from '../services/api'

type SimCardsSectionProps = {
  token: string
}

// 플랫폼별 인증 필드 정의
const PLATFORM_FIELDS: Record<string, Array<{name: string, label: string, type: string, placeholder: string, hint?: string}>> = {
  youtube: [
    { name: 'client_id', label: 'Client ID', type: 'text', placeholder: '123456789.apps.googleusercontent.com', hint: 'Google Cloud Console에서 발급받은 Client ID' },
    { name: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'GOCSPX-...', hint: 'Google Cloud Console에서 발급받은 Client Secret' },
  ],
  tiktok: [
    { name: 'app_id', label: 'App ID', type: 'text', placeholder: '1234567890', hint: 'TikTok Developer Portal에서 발급받은 App ID (10자리 이상)' },
    { name: 'app_secret', label: 'App Secret', type: 'password', placeholder: 'abcdef...', hint: 'TikTok Developer Portal에서 발급받은 App Secret' },
  ],
  instagram: [
    { name: 'app_id', label: 'App ID', type: 'text', placeholder: '123456789012345', hint: 'Facebook Developer에서 발급받은 Instagram App ID' },
    { name: 'app_secret', label: 'App Secret', type: 'password', placeholder: 'abcdef...', hint: 'Facebook Developer에서 발급받은 Instagram App Secret' },
  ],
  facebook: [
    { name: 'app_id', label: 'App ID', type: 'text', placeholder: '123456789012345', hint: 'Facebook Developer에서 발급받은 App ID' },
    { name: 'app_secret', label: 'App Secret', type: 'password', placeholder: 'abcdef...', hint: 'Facebook Developer에서 발급받은 App Secret' },
  ],
}

export function SimCardsSection({ token }: SimCardsSectionProps) {
  const [sims, setSims] = useState<SimCardItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedSim, setSelectedSim] = useState<SimCardDetailItem | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)

  // 플랫폼 계정 모달
  const [showAddPlatformAccountModal, setShowAddPlatformAccountModal] = useState(false)
  const [showEditPlatformAccountModal, setShowEditPlatformAccountModal] = useState(false)
  const [selectedPlatformAccount, setSelectedPlatformAccount] = useState<any>(null)
  const [platforms, setPlatforms] = useState<PlatformItem[]>([])

  // 검증 상태
  const [selectedPlatformCode, setSelectedPlatformCode] = useState<string>('')
  const [credentialFields, setCredentialFields] = useState<Record<string, string>>({})
  const [validationResult, setValidationResult] = useState<any>(null)
  const [validating, setValidating] = useState(false)

  // 정렬
  const [sortField, setSortField] = useState<string>('created_at')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  // SIM 번호 포맷팅 함수
  const formatSimNumber = (simNumber: string): string => {
    // 하이픈 제거
    const cleaned = simNumber.replace(/[^0-9]/g, '')
    
    // 010-XXXX-XXXX 형식으로 변환
    if (cleaned.length === 11 && cleaned.startsWith('010')) {
      return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7)}`
    }
    // 기타 형식 (예: 02-XXXX-XXXX)
    if (cleaned.length >= 9) {
      if (cleaned.startsWith('02')) {
        return `${cleaned.slice(0, 2)}-${cleaned.slice(2, 6)}-${cleaned.slice(6)}`
      }
      // 일반 전화번호 (XXX-XXXX-XXXX)
      return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7)}`
    }
    
    // 포맷할 수 없으면 원본 반환
    return simNumber
  }

  // SIM 번호 정규화 (하이픈 제거)
  const normalizeSimNumber = (simNumber: string): string => {
    return simNumber.replace(/[^0-9]/g, '')
  }

  // 플랫폼 계정 포맷팅 (YouTube(3), TikTok(2) 형식)
  const formatPlatformAccounts = (accounts: SimCardItem['platform_accounts']): string => {
    if (!accounts || accounts.length === 0) return '-'
    
    const platformGroups = accounts.reduce((acc, account) => {
      const name = account.platform_name || `Platform ${account.platform_id}`
      acc[name] = (acc[name] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    return Object.entries(platformGroups)
      .map(([name, count]) => `${name}(${count})`)
      .join(', ')
  }

  // 생성 폼
  const [newSim, setNewSim] = useState<SimCardCreateRequest>({
    sim_number: '',
    carrier: '',
    google_email: '',
    nickname: '',
    notes: '',
  })

  // 수정 폼
  const [editSim, setEditSim] = useState<SimCardUpdateRequest>({})

  useEffect(() => {
    loadSims()
    loadPlatforms()
  }, [token])

  const loadSims = async () => {
    try {
      setLoading(true)
      const data = await fetchSimCards(token, {})
      setSims(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'SIM 카드 목록 로드 실패')
    } finally {
      setLoading(false)
    }
  }

  const loadPlatforms = async () => {
    try {
      const data = await fetchPlatforms()
      setPlatforms(data)
    } catch (err) {
      console.error('플랫폼 목록 로드 실패:', err)
    }
  }

  const handleAddPlatformAccount = () => {
    if (!selectedSim) return
    // 검증 state 초기화
    setSelectedPlatformCode('')
    setCredentialFields({})
    setValidationResult(null)
    setShowAddPlatformAccountModal(true)
  }

  const handleEditPlatformAccount = (account: any) => {
    setSelectedPlatformAccount(account)
    // 검증 state 초기화
    const platform = platforms.find(p => p.id === account.platform_id)
    if (platform) {
      setSelectedPlatformCode(platform.platform_code)
    }
    setCredentialFields({})
    setValidationResult(null)
    setShowEditPlatformAccountModal(true)
  }

  const handleCreatePlatformAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedSim) return

    const form = e.target as HTMLFormElement
    const formData = new FormData(form)

    try {
      // credentialFields state에서 직접 인증 정보 가져오기
      const credentials = { ...credentialFields }

      const request: PlatformAccountCreateRequest = {
        sim_id: selectedSim.id,
        platform_id: Number(formData.get('platform_id')),
        account_name: String(formData.get('account_name')),
        account_identifier: String(formData.get('account_identifier')) || undefined,
        credentials,
        notes: String(formData.get('notes')) || undefined,
      }

      await createPlatformAccount(token, request)
      alert('플랫폼 계정이 추가되었습니다.')
      setShowAddPlatformAccountModal(false)
      
      // 새로고침
      const updated = await fetchSimCardDetail(token, selectedSim.id)
      setSelectedSim(updated)
      await loadSims()
    } catch (err) {
      alert(`추가 실패: ${(err as Error).message}`)
    }
  }

  const handleUpdatePlatformAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedPlatformAccount || !selectedSim) return

    const form = e.target as HTMLFormElement
    const formData = new FormData(form)

    try {
      // credentialFields state에서 인증 정보 가져오기 (비어있으면 undefined)
      const credentials = Object.keys(credentialFields).length > 0 ? { ...credentialFields } : undefined

      const request: PlatformAccountUpdateRequest = {
        account_name: String(formData.get('account_name')),
        account_identifier: String(formData.get('account_identifier')) || undefined,
        credentials,
        status: String(formData.get('status')) as any,
        notes: String(formData.get('notes')) || undefined,
      }

      await updatePlatformAccount(token, selectedPlatformAccount.id, request)
      alert('플랫폼 계정이 수정되었습니다.')
      setShowEditPlatformAccountModal(false)
      setSelectedPlatformAccount(null)
      
      // 새로고침
      const updated = await fetchSimCardDetail(token, selectedSim.id)
      setSelectedSim(updated)
      await loadSims()
    } catch (err) {
      alert(`수정 실패: ${(err as Error).message}`)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      // SIM 번호 정규화 (하이픈 제거)
      const normalizedSim = {
        ...newSim,
        sim_number: normalizeSimNumber(newSim.sim_number)
      }
      
      await createSimCard(token, normalizedSim)
      setNewSim({
        sim_number: '',
        carrier: '',
        google_email: '',
        nickname: '',
        notes: '',
      })
      setShowCreateForm(false)
      alert('SIM 카드가 등록되었습니다.')
      
      // 목록 새로고침 재시도 로직 (최대 3번)
      let retries = 0
      const maxRetries = 3
      while (retries < maxRetries) {
        try {
          await new Promise(resolve => setTimeout(resolve, 500)) // 0.5초 대기
          await loadSims()
          break // 성공하면 루프 종료
        } catch (reloadErr) {
          retries++
          if (retries >= maxRetries) {
            console.error('목록 새로고침 실패:', reloadErr)
            alert('목록 갱신에 실패했습니다.\n브라우저를 새로고침(F5)해주세요.')
          }
        }
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'SIM 카드 등록 실패')
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedSim) return

    try {
      await updateSimCard(token, selectedSim.id, editSim)
      setShowEditForm(false)
      setShowDetailModal(false)
      setSelectedSim(null)
      alert('SIM 카드가 수정되었습니다.')
      
      // 목록 새로고침 재시도
      let retries = 0
      while (retries < 3) {
        try {
          await new Promise(resolve => setTimeout(resolve, 500))
          await loadSims()
          break
        } catch (reloadErr) {
          retries++
          if (retries >= 3) {
            alert('목록 갱신에 실패했습니다.\n브라우저를 새로고침(F5)해주세요.')
          }
        }
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'SIM 카드 수정 실패')
    }
  }

  const handleDelete = async (simId: number) => {
    if (!confirm('정말로 이 SIM 카드를 삭제하시겠습니까?\n연결된 Agent와 계정도 함께 삭제됩니다.')) {
      return
    }

    try {
      await deleteSimCard(token, simId)
      setShowDetailModal(false)
      setSelectedSim(null)
      alert('SIM 카드가 삭제되었습니다.')
      
      // 목록 새로고침 재시도
      let retries = 0
      while (retries < 3) {
        try {
          await new Promise(resolve => setTimeout(resolve, 500))
          await loadSims()
          break
        } catch (reloadErr) {
          retries++
          if (retries >= 3) {
            alert('목록 갱신에 실패했습니다.\n브라우저를 새로고침(F5)해주세요.')
          }
        }
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'SIM 카드 삭제 실패')
    }
  }

  const handleShowDetail = async (simId: number) => {
    try {
      // 재시도 로직
      let retries = 0
      let detail = null
      while (retries < 3) {
        try {
          detail = await fetchSimCardDetail(token, simId)
          break
        } catch (err) {
          retries++
          if (retries < 3) {
            await new Promise(resolve => setTimeout(resolve, 500))
          } else {
            throw err
          }
        }
      }
      
      if (detail) {
        setSelectedSim(detail)
        setShowDetailModal(true)
        setEditSim({
          carrier: detail.carrier || '',
          google_email: detail.google_email || '',
          google_account_status: detail.google_account_status as 'active' | 'banned' | 'suspended',
          nickname: detail.nickname || '',
          notes: detail.notes || '',
          status: detail.status as 'active' | 'inactive' | 'banned',
        })
      }
    } catch (err) {
      console.error('상세 조회 실패:', err)
      alert(err instanceof Error ? err.message : 'SIM 카드 상세 조회 실패. 잠시 후 다시 시도해주세요.')
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'badge badge-success',
      inactive: 'badge badge-secondary',
      banned: 'badge badge-danger',
      expired: 'badge badge-warning',
    }
    const labels: Record<string, string> = {
      active: '🟢 정상',
      inactive: '⚪ 비활성',
      banned: '🔴 차단',
      expired: '🟠 만료',
    }
    return <span className={styles[status] || 'badge'}>{labels[status] || status}</span>
  }

  const getAgentStatusBadge = (agentStatus: string) => {
    const styles: Record<string, string> = {
      online: 'badge badge-success',
      offline: 'badge badge-secondary',
      not_registered: 'badge badge-warning',
    }
    const labels: Record<string, string> = {
      online: '온라인',
      offline: '오프라인',
      not_registered: '미등록',
    }
    return <span className={styles[agentStatus] || 'badge'}>{labels[agentStatus] || agentStatus}</span>
  }

  // 정렬 핸들러
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // 정렬 아이콘
  const getSortIcon = (field: string) => {
    if (sortField !== field) return ' ⇅'
    return sortDirection === 'asc' ? ' ▲' : ' ▼'
  }

  // 정렬된 SIM 목록
  const sortedSims = [...sims].sort((a, b) => {
    let aVal: any = a[sortField as keyof SimCardItem]
    let bVal: any = b[sortField as keyof SimCardItem]

    // null/undefined 처리
    if (aVal === null || aVal === undefined) aVal = ''
    if (bVal === null || bVal === undefined) bVal = ''

    // 숫자 비교
    if (sortField === 'total_accounts') {
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
    }

    // 문자열 비교
    const comparison = String(aVal).localeCompare(String(bVal))
    return sortDirection === 'asc' ? comparison : -comparison
  })

  return (
    <div className="section">
      <div className="section-header">
        <div>
          <h2>SIM 카드 관리</h2>
          <p className="section-subtitle">사용자의 SIM 카드를 관리합니다 (v2.0 Architecture)</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
          {showCreateForm ? '취소' : '+ SIM 추가'}
        </button>
      </div>

      {/* 생성 폼 */}
      {showCreateForm && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h3>새 SIM 카드 등록</h3>
          <form onSubmit={handleCreate}>
            <div className="form-row">
              <div className="form-group">
                <label>SIM 번호 (필수)</label>
                <input
                  type="text"
                  value={newSim.sim_number}
                  onChange={(e) => setNewSim({ ...newSim, sim_number: e.target.value })}
                  placeholder="010-1234-5678"
                  required
                />
              </div>
              <div className="form-group">
                <label>통신사</label>
                <select
                  value={newSim.carrier}
                  onChange={(e) => setNewSim({ ...newSim, carrier: e.target.value })}
                >
                  <option value="">선택</option>
                  <option value="SKT">SKT</option>
                  <option value="KT">KT</option>
                  <option value="LG U+">LG U+</option>
                  <option value="알뜰폰">알뜰폰</option>
                  <option value="해외">해외</option>
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Google 이메일</label>
                <input
                  type="email"
                  value={newSim.google_email}
                  onChange={(e) => setNewSim({ ...newSim, google_email: e.target.value })}
                  placeholder="example@gmail.com"
                />
              </div>
              <div className="form-group">
                <label>별칭</label>
                <input
                  type="text"
                  value={newSim.nickname}
                  onChange={(e) => setNewSim({ ...newSim, nickname: e.target.value })}
                  placeholder="게임 채널용 SIM"
                />
              </div>
            </div>
            <div className="form-group">
              <label>메모</label>
              <textarea
                value={newSim.notes}
                onChange={(e) => setNewSim({ ...newSim, notes: e.target.value })}
                placeholder="메모 입력"
                rows={2}
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">
                등록
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowCreateForm(false)}>
                취소
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 액션 버튼 */}
      <div className="section-actions" style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem' }}>
        <button className="btn btn-secondary" onClick={loadSims}>
          🔄 새로고침
        </button>
      </div>

      {loading && <p>로딩 중...</p>}
      {error && <p className="error">{error}</p>}

      {/* SIM 목록 - 테이블 형식 */}
      {!loading && !error && (
        <div className="table-container">
          {sims.length === 0 ? (
            <p className="no-data">등록된 SIM 카드가 없습니다.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '60px' }}>순번</th>
                  <th 
                    style={{ width: '100px', cursor: 'pointer' }} 
                    onClick={() => handleSort('status')}
                    title="클릭하여 정렬"
                  >
                    상태{getSortIcon('status')}
                  </th>
                  <th 
                    style={{ width: '140px', cursor: 'pointer' }} 
                    onClick={() => handleSort('sim_number')}
                    title="클릭하여 정렬"
                  >
                    SIM 번호{getSortIcon('sim_number')}
                  </th>
                  <th 
                    style={{ width: '100px', cursor: 'pointer' }} 
                    onClick={() => handleSort('carrier')}
                    title="클릭하여 정렬"
                  >
                    통신사{getSortIcon('carrier')}
                  </th>
                  <th 
                    style={{ minWidth: '200px', cursor: 'pointer' }} 
                    onClick={() => handleSort('google_email')}
                    title="클릭하여 정렬"
                  >
                    Google 계정{getSortIcon('google_email')}
                  </th>
                  <th 
                    style={{ width: '120px', cursor: 'pointer' }} 
                    onClick={() => handleSort('agent_status')}
                    title="클릭하여 정렬"
                  >
                    Agent 상태{getSortIcon('agent_status')}
                  </th>
                  <th 
                    style={{ width: '180px', cursor: 'pointer'}} 
                    onClick={() => handleSort('total_accounts')}
                    title="클릭하여 정렬"
                  >
                    등록된 플랫폼{getSortIcon('total_accounts')}
                  </th>
                  <th style={{ minWidth: '150px' }}>별칭/메모</th>
                  <th style={{ width: '120px' }}>작업</th>
                </tr>
              </thead>
              <tbody>
                {sortedSims.map((sim, index) => (
                  <tr key={sim.id} className="table-row-hover">
                    <td className="text-center">{index + 1}</td>
                    <td className="text-center">{getStatusBadge(sim.status)}</td>
                    <td className="text-bold">{formatSimNumber(sim.sim_number)}</td>
                    <td className="text-center">{sim.carrier || '-'}</td>
                    <td className="text-small">{sim.google_email || '-'}</td>
                    <td className="text-center">{getAgentStatusBadge(sim.agent_status)}</td>
                    <td className="text-small">{formatPlatformAccounts(sim.platform_accounts)}</td>
                    <td className="text-small">{sim.nickname || sim.notes || '-'}</td>
                    <td className="text-center">
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => handleShowDetail(sim.id)}
                        title="상세 보기"
                      >
                        상세
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* 상세 모달 */}
      {showDetailModal && selectedSim && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedSim.display_name} 상세 정보</h2>
              <button className="btn-close" onClick={() => setShowDetailModal(false)}>
                ×
              </button>
            </div>

            {!showEditForm ? (
              <>
                <div className="modal-body">
                  <h3>기본 정보</h3>
                  <p>
                    <strong>SIM 번호:</strong> {formatSimNumber(selectedSim.sim_number)}
                  </p>
                  <p>
                    <strong>통신사:</strong> {selectedSim.carrier || 'N/A'}
                  </p>
                  <p>
                    <strong>Google 이메일:</strong> {selectedSim.google_email || 'N/A'}
                  </p>
                  <p>
                    <strong>Google 계정 상태:</strong> {getStatusBadge(selectedSim.google_account_status)}
                  </p>
                  <p>
                    <strong>상태:</strong> {getStatusBadge(selectedSim.status)}
                  </p>
                  <p>
                    <strong>생성일:</strong> {new Date(selectedSim.created_at).toLocaleString()}
                  </p>

                  {selectedSim.agent && (
                    <>
                      <h3 style={{ marginTop: '1.5rem' }}>연결된 Agent</h3>
                      <p>
                        <strong>디바이스명:</strong> {selectedSim.agent.device_name}
                      </p>
                      <p>
                        <strong>상태:</strong> {getStatusBadge(selectedSim.agent.status)}
                      </p>
                      <p>
                        <strong>마지막 Heartbeat:</strong>{' '}
                        {selectedSim.agent.last_heartbeat ? new Date(selectedSim.agent.last_heartbeat).toLocaleString() : 'N/A'}
                      </p>
                    </>
                  )}

                  <h3 style={{ marginTop: '1.5rem' }}>등록된 플랫폼 계정 ({selectedSim.platform_accounts.length}개)</h3>
                  {selectedSim.platform_accounts.length === 0 ? (
                    <p>등록된 계정이 없습니다.</p>
                  ) : (
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      <table className="data-table" style={{ marginTop: '0.5rem' }}>
                        <thead>
                          <tr style={{ position: 'sticky', top: 0, background: 'var(--color-bg-header)', zIndex: 1 }}>
                            <th>플랫폼</th>
                            <th>계정명</th>
                            <th>계정 ID</th>
                            <th>상태</th>
                            <th>마지막 검증</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedSim.platform_accounts.map((acc) => (
                            <tr key={acc.id}>
                              <td className="text-bold">{acc.platform_name || `Platform ${acc.platform_id}`}</td>
                              <td>{acc.account_name}</td>
                              <td className="text-small">{acc.account_identifier || '-'}</td>
                              <td className="text-center">{getStatusBadge(acc.status)}</td>
                              <td className="text-small text-center">
                                {acc.last_validated ? new Date(acc.last_validated).toLocaleString('ko-KR', { 
                                  year: '2-digit', 
                                  month: '2-digit', 
                                  day: '2-digit',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                }) : '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <div className="modal-footer">
                  <button className="btn btn-primary" onClick={() => setShowEditForm(true)}>
                    수정
                  </button>
                  <button className="btn btn-danger" onClick={() => handleDelete(selectedSim.id)}>
                    삭제
                  </button>
                  <button className="btn btn-secondary" onClick={() => setShowDetailModal(false)}>
                    닫기
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="modal-body">
                  <form onSubmit={handleUpdate}>
                    <div className="form-group">
                      <label>통신사</label>
                      <select
                        value={editSim.carrier}
                        onChange={(e) => setEditSim({ ...editSim, carrier: e.target.value })}
                      >
                        <option value="">선택</option>
                        <option value="SKT">SKT</option>
                        <option value="KT">KT</option>
                        <option value="LG U+">LG U+</option>
                        <option value="알뜰폰">알뜰폰</option>
                        <option value="해외">해외</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Google 이메일</label>
                      <input
                        type="email"
                        value={editSim.google_email}
                        onChange={(e) => setEditSim({ ...editSim, google_email: e.target.value })}
                      />
                    </div>
                    <div className="form-group">
                      <label>Google 계정 상태</label>
                      <select
                        value={editSim.google_account_status}
                        onChange={(e) => setEditSim({ ...editSim, google_account_status: e.target.value as 'active' | 'banned' | 'suspended' })}
                      >
                        <option value="active">Active</option>
                        <option value="banned">Banned</option>
                        <option value="suspended">Suspended</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>별칭</label>
                      <input
                        type="text"
                        value={editSim.nickname}
                        onChange={(e) => setEditSim({ ...editSim, nickname: e.target.value })}
                      />
                    </div>
                    <div className="form-group">
                      <label>상태</label>
                      <select
                        value={editSim.status}
                        onChange={(e) => setEditSim({ ...editSim, status: e.target.value as 'active' | 'inactive' | 'banned' })}
                      >
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="banned">Banned</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>메모</label>
                      <textarea
                        value={editSim.notes}
                        onChange={(e) => setEditSim({ ...editSim, notes: e.target.value })}
                        rows={3}
                      />
                    </div>

                    {/* 등록된 플랫폼 계정 관리 */}
                    <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3 style={{ margin: 0 }}>등록된 플랫폼 계정 ({selectedSim.platform_accounts.length}개)</h3>
                        <button
                          type="button"
                          className="btn btn-sm btn-success"
                          onClick={handleAddPlatformAccount}
                        >
                          + 플랫폼 계정 추가
                        </button>
                      </div>
                      {selectedSim.platform_accounts.length === 0 ? (
                        <p style={{ color: '#999', fontSize: '0.9rem' }}>등록된 계정이 없습니다.</p>
                      ) : (
                        <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                          <table className="data-table" style={{ marginTop: '0.5rem' }}>
                            <thead>
                              <tr style={{ position: 'sticky', top: 0, background: 'var(--color-bg-header)', zIndex: 1 }}>
                                <th>플랫폼</th>
                                <th>계정명</th>
                                <th>계정 ID</th>
                                <th>상태</th>
                                <th style={{ width: '140px' }}>작업</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedSim.platform_accounts.map((acc) => (
                                <tr key={acc.id}>
                                  <td className="text-bold">{acc.platform_name || `Platform ${acc.platform_id}`}</td>
                                  <td>{acc.account_name}</td>
                                  <td className="text-small">{acc.account_identifier || '-'}</td>
                                  <td className="text-center">{getStatusBadge(acc.status)}</td>
                                  <td className="text-center">
                                    <div className="btn-group">
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-primary"
                                        onClick={() => handleEditPlatformAccount(acc)}
                                        title="수정"
                                      >
                                        수정
                                      </button>
                                      <button
                                        type="button"
                                        className="btn btn-sm btn-danger"
                                        onClick={async () => {
                                          if (!window.confirm(`플랫폼 계정 "${acc.account_name}"을(를) 삭제하시겠습니까?`)) return
                                          try {
                                            await deletePlatformAccount(token, acc.id)
                                            alert('플랫폼 계정이 삭제되었습니다.')
                                            const updated = await fetchSimCardDetail(token, selectedSim.id)
                                            setSelectedSim(updated)
                                            await loadSims()
                                          } catch (err) {
                                            alert(`삭제 실패: ${(err as Error).message}`)
                                          }
                                        }}
                                        title="삭제"
                                      >
                                        삭제
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                    <div className="form-actions">
                      <button type="submit" className="btn btn-primary">
                        저장
                      </button>
                      <button type="button" className="btn btn-secondary" onClick={() => setShowEditForm(false)}>
                        취소
                      </button>
                    </div>
                  </form>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* 통계 */}
      <div className="section-footer">
        <p>
          총 {sims.length}개 SIM | 활성: {sims.filter((s) => s.status === 'active').length}개 | 비활성:{' '}
          {sims.filter((s) => s.status === 'inactive').length}개 | 차단: {sims.filter((s) => s.status === 'banned').length}개
        </p>
      </div>

      {/* 플랫폼 계정 추가 모달 */}
      {showAddPlatformAccountModal && selectedSim && (
        <div className="modal-overlay" onClick={() => setShowAddPlatformAccountModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>플랫폼 계정 추가</h3>
              <button className="modal-close" onClick={() => setShowAddPlatformAccountModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleCreatePlatformAccount}>
              <div className="modal-body">
                <div className="form-group">
                  <label>플랫폼 <span className="text-danger">*</span></label>
                  <select 
                    name="platform_id" 
                    className="form-control" 
                    required
                    onChange={(e) => {
                      const platformId = parseInt(e.target.value)
                      const platform = platforms.find(p => p.id === platformId)
                      if (platform) {
                        setSelectedPlatformCode(platform.platform_code)
                        setCredentialFields({})
                        setValidationResult(null)
                      }
                    }}
                  >
                    <option value="">선택</option>
                    {platforms.filter(p => p.is_active).map((platform) => (
                      <option key={platform.id} value={platform.id}>
                        {platform.platform_name}
                      </option>
                    ))}
                  </select>
                  <small className="form-text">업로드할 플랫폼을 선택하세요</small>
                </div>

                <div className="form-group">
                  <label>계정명 <span className="text-danger">*</span></label>
                  <input
                    type="text"
                    name="account_name"
                    className="form-control"
                    placeholder="예: 내 유튜브 계정"
                    required
                  />
                  <small className="form-text">식별하기 쉬운 이름을 입력하세요</small>
                </div>

                <div className="form-group">
                  <label>계정 ID / 채널 ID</label>
                  <input
                    type="text"
                    name="account_identifier"
                    className="form-control"
                    placeholder="예: UCxxxxxxxxxxxxxx (YouTube), @username (TikTok)"
                  />
                  <small className="form-text">채널 ID, 사용자명 등</small>
                </div>

                {/* 플랫폼별 인증 필드 */}
                {selectedPlatformCode && PLATFORM_FIELDS[selectedPlatformCode] && (
                  <div>
                    <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem', fontSize: '1rem', fontWeight: 'bold' }}>
                      인증 정보 <span className="text-danger">*</span>
                    </h4>
                    {PLATFORM_FIELDS[selectedPlatformCode].map((field) => (
                      <div key={field.name} className="form-group">
                        <label>{field.label} <span className="text-danger">*</span></label>
                        <input
                          type={field.type}
                          name={`credential_${field.name}`}
                          className="form-control"
                          placeholder={field.placeholder}
                          required
                          value={credentialFields[field.name] || ''}
                          onChange={(e) => {
                            setCredentialFields({
                              ...credentialFields,
                              [field.name]: e.target.value
                            })
                            setValidationResult(null)
                          }}
                        />
                        {field.hint && (
                          <small className="form-text">{field.hint}</small>
                        )}
                      </div>
                    ))}
                    
                    {/* 검증 테스트 버튼 */}
                    <div style={{ marginTop: '0.75rem' }}>
                      <button
                        type="button"
                        className="btn btn-info"
                        disabled={validating || Object.keys(credentialFields).length === 0}
                        onClick={async () => {
                          const form = document.querySelector('form') as HTMLFormElement
                          const platformId = (form.platform_id as any).value
                          
                          if (!platformId) {
                            alert('플랫폼을 먼저 선택하세요')
                            return
                          }
                          
                          try {
                            setValidating(true)
                            const result = await validatePlatformCredentials(token, parseInt(platformId), credentialFields)
                            setValidationResult(result)
                          } catch (err) {
                            setValidationResult({
                              valid: false,
                              errors: [err instanceof Error ? err.message : '검증 요청 실패'],
                              warnings: [],
                              checked_fields: [],
                              missing_fields: [],
                            })
                          } finally {
                            setValidating(false)
                          }
                        }}
                      >
                        {validating ? '검증 중...' : '🔍 인증 정보 테스트'}
                      </button>
                    </div>
                    
                    {/* 검증 결과 표시 */}
                    {validationResult && (
                      <div
                        className={`alert ${validationResult.valid ? 'alert-success' : 'alert-danger'}`}
                        style={{ marginTop: '0.75rem', padding: '0.75rem', borderRadius: '0.25rem' }}
                      >
                        <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                          {validationResult.valid ? '✅ 검증 성공' : '❌ 검증 실패'}
                        </h4>
                        
                        {validationResult.errors && validationResult.errors.length > 0 && (
                          <div>
                            <strong style={{ color: '#dc3545' }}>오류:</strong>
                            <ul style={{ marginBottom: '0.5rem', paddingLeft: '1.5rem' }}>
                              {validationResult.errors.map((err: string, idx: number) => (
                                <li key={idx} style={{ color: '#dc3545' }}>{err}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {validationResult.warnings && validationResult.warnings.length > 0 && (
                          <div>
                            <strong style={{ color: '#ffc107' }}>경고:</strong>
                            <ul style={{ marginBottom: '0.5rem', paddingLeft: '1.5rem' }}>
                              {validationResult.warnings.map((warn: string, idx: number) => (
                                <li key={idx} style={{ color: '#856404' }}>{warn}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {validationResult.valid && (
                          <div style={{ fontSize: '0.85rem', color: '#155724' }}>
                            확인된 필드: {validationResult.checked_fields?.join(', ')}
                          </div>
                        )}
                        
                        {validationResult.missing_fields && validationResult.missing_fields.length > 0 && (
                          <div style={{ fontSize: '0.85rem', color: '#dc3545' }}>
                            누락된 필수 필드: {validationResult.missing_fields.join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                <div className="form-group">
                  <label>메모</label>
                  <textarea
                    name="notes"
                    className="form-control"
                    rows={2}
                    placeholder="계정에 대한 메모"
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddPlatformAccountModal(false)}>
                  취소
                </button>
                <button type="submit" className="btn btn-primary">
                  추가
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 플랫폼 계정 수정 모달 */}
      {showEditPlatformAccountModal && selectedPlatformAccount && selectedSim && (
        <div className="modal-overlay" onClick={() => setShowEditPlatformAccountModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>플랫폼 계정 수정</h3>
              <button className="modal-close" onClick={() => setShowEditPlatformAccountModal(false)}>
                ×
              </button>
            </div>
            <form onSubmit={handleUpdatePlatformAccount}>
              <div className="modal-body">
                <div className="form-group">
                  <label>플랫폼</label>
                  <input
                    type="text"
                    className="form-control"
                    value={selectedPlatformAccount.platform_name || `Platform ${selectedPlatformAccount.platform_id}`}
                    disabled
                    style={{ backgroundColor: '#f0f0f0' }}
                  />
                </div>

                <div className="form-group">
                  <label>계정명 <span className="text-danger">*</span></label>
                  <input
                    type="text"
                    name="account_name"
                    className="form-control"
                    defaultValue={selectedPlatformAccount.account_name}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>계정 ID / 채널 ID</label>
                  <input
                    type="text"
                    name="account_identifier"
                    className="form-control"
                    defaultValue={selectedPlatformAccount.account_identifier || ''}
                    placeholder="예: UCxxxxxxxxxxxxxx (YouTube), @username (TikTok)"
                  />
                </div>

                <div className="form-group">
                  <label>상태</label>
                  <select name="status" className="form-control" defaultValue={selectedPlatformAccount.status}>
                    <option value="active">🟢 정상 (Active)</option>
                    <option value="inactive">⚪ 비활성 (Inactive)</option>
                    <option value="banned">🔴 차단 (Banned)</option>
                    <option value="expired">🟠 만료 (Expired)</option>
                  </select>
                  <small className="form-text">계정의 현재 상태를 선택하세요</small>
                </div>

                {/* 플랫폼별 인증 필드 */}
                {selectedPlatformCode && PLATFORM_FIELDS[selectedPlatformCode] && (
                  <div>
                    <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem', fontSize: '1rem', fontWeight: 'bold' }}>
                      인증 정보 (선택)
                    </h4>
                    <small className="form-text" style={{ display: 'block', marginBottom: '1rem' }}>
                      변경할 경우만 입력하세요. 비워두면 기존 값이 유지됩니다.
                    </small>
                    {PLATFORM_FIELDS[selectedPlatformCode].map((field) => (
                      <div key={field.name} className="form-group">
                        <label>{field.label}</label>
                        <input
                          type={field.type}
                          name={`credential_${field.name}`}
                          className="form-control"
                          placeholder={field.placeholder}
                          value={credentialFields[field.name] || ''}
                          onChange={(e) => {
                            setCredentialFields({
                              ...credentialFields,
                              [field.name]: e.target.value
                            })
                            setValidationResult(null)
                          }}
                        />
                        {field.hint && (
                          <small className="form-text">{field.hint}</small>
                        )}
                      </div>
                    ))}
                    
                    {/* 검증 테스트 버튼 */}
                    {Object.keys(credentialFields).length > 0 && (
                      <div style={{ marginTop: '0.75rem' }}>
                        <button
                          type="button"
                          className="btn btn-info"
                          disabled={validating}
                          onClick={async () => {
                            try {
                              setValidating(true)
                              const result = await validatePlatformCredentials(
                                token,
                                selectedPlatformAccount.platform_id,
                                credentialFields
                              )
                              setValidationResult(result)
                            } catch (err) {
                              setValidationResult({
                                valid: false,
                                errors: [err instanceof Error ? err.message : '검증 요청 실패'],
                                warnings: [],
                                checked_fields: [],
                                missing_fields: [],
                              })
                            } finally {
                              setValidating(false)
                            }
                          }}
                        >
                          {validating ? '검증 중...' : '🔍 인증 정보 테스트'}
                        </button>
                      </div>
                    )}
                    
                    {/* 검증 결과 표시 */}
                    {validationResult && (
                      <div
                        className={`alert ${validationResult.valid ? 'alert-success' : 'alert-danger'}`}
                        style={{ marginTop: '0.75rem', padding: '0.75rem', borderRadius: '0.25rem' }}
                      >
                        <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                          {validationResult.valid ? '✅ 검증 성공' : '❌ 검증 실패'}
                        </h4>
                        
                        {validationResult.errors && validationResult.errors.length > 0 && (
                          <div>
                            <strong style={{ color: '#dc3545' }}>오류:</strong>
                            <ul style={{ marginBottom: '0.5rem', paddingLeft: '1.5rem' }}>
                              {validationResult.errors.map((err: string, idx: number) => (
                                <li key={idx} style={{ color: '#dc3545' }}>{err}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {validationResult.warnings && validationResult.warnings.length > 0 && (
                          <div>
                            <strong style={{ color: '#ffc107' }}>경고:</strong>
                            <ul style={{ marginBottom: '0.5rem', paddingLeft: '1.5rem' }}>
                              {validationResult.warnings.map((warn: string, idx: number) => (
                                <li key={idx} style={{ color: '#856404' }}>{warn}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {validationResult.valid && (
                          <div style={{ fontSize: '0.85rem', color: '#155724' }}>
                            확인된 필드: {validationResult.checked_fields?.join(', ')}
                          </div>
                        )}
                        
                        {validationResult.missing_fields && validationResult.missing_fields.length > 0 && (
                          <div style={{ fontSize: '0.85rem', color: '#dc3545' }}>
                            누락된 필수 필드: {validationResult.missing_fields.join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                <div className="form-group">
                  <label>메모</label>
                  <textarea
                    name="notes"
                    className="form-control"
                    rows={2}
                    defaultValue={selectedPlatformAccount.notes || ''}
                    placeholder="계정에 대한 메모"
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEditPlatformAccountModal(false)}>
                  취소
                </button>
                <button type="submit" className="btn btn-primary">
                  수정
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
