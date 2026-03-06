import { useState, useEffect } from 'react'
import {
  fetchPlatforms,
  fetchSimCards,
  fetchPlatformAccounts,
  createPlatformAccount,
  deletePlatformAccount,
  banPlatformAccount,
  activatePlatformAccount,
  type PlatformItem,
  type SimCardItem,
  type PlatformAccountItem,
  type PlatformAccountCreateRequest,
} from '../services/api'
import './SectionStyles.css'

type MessageType = { type: 'success' | 'error'; text: string }

interface Props {
  token: string
}

export function PlatformAccountsSection({ token }: Props) {
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<MessageType | null>(null)
  
  // 데이터
  const [platforms, setPlatforms] = useState<PlatformItem[]>([])
  const [sims, setSims] = useState<SimCardItem[]>([])
  const [accounts, setAccounts] = useState<PlatformAccountItem[]>([])
  
  // 필터
  const [platformFilter, setPlatformFilter] = useState<number | null>(null)
  const [simFilter, setSimFilter] = useState<number | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  
  // 폼 상태
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newAccount, setNewAccount] = useState<Partial<PlatformAccountCreateRequest>>({
    sim_id: undefined,
    platform_id: undefined,
    account_name: '',
    account_identifier: '',
    credentials: {},
    is_primary: false,
  })
  
  // 상세 모달
  const [selectedAccount, setSelectedAccount] = useState<PlatformAccountItem | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  
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
      const [platformsData, simsData, accountsData] = await Promise.all([
        fetchPlatforms(),
        fetchSimCards(token),
        fetchPlatformAccounts(token, {
          platform_id: platformFilter || undefined,
          sim_id: simFilter || undefined,
          status_filter: statusFilter || undefined,
        }),
      ])
      setPlatforms(platformsData)
      setSims(simsData)
      setAccounts(accountsData)
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newAccount.sim_id || !newAccount.platform_id || !newAccount.account_name) {
      setMessage({ type: 'error', text: 'SIM, 플랫폼, 계정명은 필수입니다' })
      return
    }

    try {
      setLoading(true)
      // 1 SIM = 1 YouTube 계정이므로 항상 주 계정으로 설정
      await createPlatformAccount(token, { ...newAccount, is_primary: true } as PlatformAccountCreateRequest)
      setMessage({ type: 'success', text: '플랫폼 계정이 생성되었습니다' })
      setShowCreateForm(false)
      setNewAccount({
        sim_id: undefined,
        platform_id: undefined,
        account_name: '',
        account_identifier: '',
        credentials: {},
        is_primary: false,
      })
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (accountId: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return

    try {
      setLoading(true)
      await deletePlatformAccount(token, accountId)
      setMessage({ type: 'success', text: '계정이 삭제되었습니다' })
      setShowDetailModal(false)
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handleBan = async (accountId: number) => {
    if (!confirm('이 계정을 BAN 처리하시겠습니까?')) return

    try {
      setLoading(true)
      await banPlatformAccount(token, accountId, 'Manual BAN by admin')
      setMessage({ type: 'success', text: '계정이 BAN 처리되었습니다' })
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handleActivate = async (accountId: number) => {
    try {
      setLoading(true)
      await activatePlatformAccount(token, accountId)
      setMessage({ type: 'success', text: '계정이 활성화되었습니다' })
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      inactive: 'gray',
      banned: 'red',
      suspended: 'orange',
    }
    return (
      <span className={`badge badge-${colors[status] || 'gray'}`}>
        {status.toUpperCase()}
      </span>
    )
  }

  const getPlatformName = (platformId: number) => {
    return platforms.find((p) => p.id === platformId)?.platform_name || 'Unknown'
  }

  const getSimNumber = (simId: number) => {
    return sims.find((s) => s.id === simId)?.sim_number || 'Unknown'
  }

  return (
    <div className="section-container">
      <header className="section-header">
        <h2>📱 플랫폼 계정 관리 (SIM 기반)</h2>
        <button className="btn btn-primary" onClick={() => setShowCreateForm(true)}>
          + 계정 추가
        </button>
      </header>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 필터 */}
      <div className="filter-bar">
        <select value={platformFilter || ''} onChange={(e) => setPlatformFilter(e.target.value ? Number(e.target.value) : null)}>
          <option value="">전체 플랫폼</option>
          {platforms.map((p) => (
            <option key={p.id} value={p.id}>{p.platform_name}</option>
          ))}
        </select>
        <select value={simFilter || ''} onChange={(e) => setSimFilter(e.target.value ? Number(e.target.value) : null)}>
          <option value="">전체 SIM</option>
          {sims.map((s) => (
            <option key={s.id} value={s.id}>{s.sim_number}</option>
          ))}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">전체 상태</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="banned">Banned</option>
        </select>
        <button className="btn btn-secondary" onClick={loadData}>🔄 새로고침</button>
      </div>

      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : (
        <div className="cards-grid">
          {accounts.length === 0 ? (
            <div className="empty-state">
              <p>등록된 플랫폼 계정이 없습니다.</p>
              <p>SIM 카드를 먼저 등록한 후 플랫폼 계정을 추가하세요.</p>
            </div>
          ) : (
            accounts.map((account) => (
              <div key={account.id} className="card card-clickable" onClick={() => {
                setSelectedAccount(account)
                setShowDetailModal(true)
              }}>
                <div className="card-header">
                  <h3>{account.account_name}</h3>
                  {getStatusBadge(account.status)}
                </div>
                <div className="card-body">
                  <p><strong>플랫폼:</strong> {getPlatformName(account.platform_id)}</p>
                  <p><strong>SIM:</strong> {getSimNumber(account.sim_id)}</p>
                  {account.account_identifier && (
                    <p><strong>채널 ID:</strong> {account.account_identifier}</p>
                  )}
                  {account.ban_detected_at && (
                    <p className="text-danger">
                      <strong>BAN 감지:</strong> {new Date(account.ban_detected_at).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 생성 폼 모달 */}
      {showCreateForm && (
        <div className="modal-overlay" onClick={() => setShowCreateForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>플랫폼 계정 추가</h3>
              <button className="btn-close" onClick={() => setShowCreateForm(false)}>×</button>
            </div>
            <form onSubmit={handleCreate} className="modal-body">
              <div className="form-group">
                <label>SIM 카드 *</label>
                <select
                  required
                  value={newAccount.sim_id || ''}
                  onChange={(e) => setNewAccount({ ...newAccount, sim_id: Number(e.target.value) })}
                >
                  <option value="">SIM 선택</option>
                  {sims.filter((s) => s.status === 'active').map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.sim_number} ({s.carrier}) - {s.nickname || '이름 없음'}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>플랫폼 *</label>
                <select
                  required
                  value={newAccount.platform_id || ''}
                  onChange={(e) => setNewAccount({ ...newAccount, platform_id: Number(e.target.value) })}
                >
                  <option value="">플랫폼 선택</option>
                  {platforms.filter((p) => p.is_active).map((p) => (
                    <option key={p.id} value={p.id}>{p.platform_name}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>YouTube 계정 이메일 또는 채널명 *</label>
                <input
                  type="text"
                  required
                  placeholder="예: example@gmail.com 또는 채널 이름"
                  value={newAccount.account_name || ''}
                  onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })}
                />
                <small className="help-text">
                  YouTube 로그인에 사용하는 Google 계정 이메일 또는 채널명을 입력하세요
                </small>
              </div>
              
              <div className="form-group">
                <label>YouTube 채널 ID 또는 사용자명 (선택)</label>
                <input
                  type="text"
                  placeholder="예: UC1234567890 또는 @username"
                  value={newAccount.account_identifier || ''}
                  onChange={(e) => setNewAccount({ ...newAccount, account_identifier: e.target.value })}
                />
                <small className="help-text">
                  채널 페이지 주소에서 확인할 수 있는 채널 ID(UC로 시작) 또는 @로 시작하는 사용자명을 입력하세요. 선택사항입니다.
                </small>
              </div>
              
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateForm(false)}>
                  취소
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? '생성 중...' : '생성'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 상세 모달 */}
      {showDetailModal && selectedAccount && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedAccount.account_name}</h3>
              <button className="btn-close" onClick={() => setShowDetailModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h4>기본 정보</h4>
                <table className="detail-table">
                  <tbody>
                    <tr>
                      <th>ID</th>
                      <td>{selectedAccount.id}</td>
                    </tr>
                    <tr>
                      <th>플랫폼</th>
                      <td>{getPlatformName(selectedAccount.platform_id)}</td>
                    </tr>
                    <tr>
                      <th>SIM 카드</th>
                      <td>{getSimNumber(selectedAccount.sim_id)}</td>
                    </tr>
                    <tr>
                      <th>계정명</th>
                      <td>{selectedAccount.account_name}</td>
                    </tr>
                    <tr>
                      <th>식별자</th>
                      <td>{selectedAccount.account_identifier || '-'}</td>
                    </tr>
                    <tr>
                      <th>상태</th>
                      <td>{getStatusBadge(selectedAccount.status)}</td>
                    </tr>
                    <tr>
                      <th>Primary</th>
                      <td>{selectedAccount.is_primary ? '예' : '아니오'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              {selectedAccount.ban_detected_at && (
                <div className="detail-section alert alert-danger">
                  <h4>🚫 BAN 정보</h4>
                  <p><strong>감지일:</strong> {new Date(selectedAccount.ban_detected_at).toLocaleString()}</p>
                  <p><strong>사유:</strong> {selectedAccount.ban_reason || '알 수 없음'}</p>
                </div>
              )}
              
              <div className="detail-section">
                <h4>사용 이력</h4>
                <table className="detail-table">
                  <tbody>
                    <tr>
                      <th>마지막 검증</th>
                      <td>{selectedAccount.last_validated ? new Date(selectedAccount.last_validated).toLocaleString() : '-'}</td>
                    </tr>
                    <tr>
                      <th>마지막 사용</th>
                      <td>{selectedAccount.last_used ? new Date(selectedAccount.last_used).toLocaleString() : '-'}</td>
                    </tr>
                    <tr>
                      <th>생성일</th>
                      <td>{new Date(selectedAccount.created_at).toLocaleString()}</td>
                    </tr>
                    <tr>
                      <th>수정일</th>
                      <td>{new Date(selectedAccount.updated_at).toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              {selectedAccount.notes && (
                <div className="detail-section">
                  <h4>메모</h4>
                  <p>{selectedAccount.notes}</p>
                </div>
              )}
              
              <div className="form-actions">
                {selectedAccount.status === 'active' ? (
                  <button className="btn btn-danger" onClick={() => handleBan(selectedAccount.id)}>
                    🚫 BAN 처리
                  </button>
                ) : (
                  <button className="btn btn-success" onClick={() => handleActivate(selectedAccount.id)}>
                    ✅ 활성화
                  </button>
                )}
                <button className="btn btn-danger" onClick={() => handleDelete(selectedAccount.id)}>
                  🗑️ 삭제
                </button>
                <button className="btn btn-secondary" onClick={() => setShowDetailModal(false)}>
                  닫기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
