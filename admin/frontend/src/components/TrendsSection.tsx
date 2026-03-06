import { useState, useEffect } from 'react'
import { fetchTrends, collectTrends, type TrendItem } from '../services/api'
import './SectionStyles.css'

type MessageType = { type: 'success' | 'error'; text: string }

interface Props {
  token: string
  username: string
}

// 주요 국가/지역 코드 목록
const REGION_CODES = [
  { code: 'KR', name: '🇰🇷 대한민국 (Korea)' },
  { code: 'US', name: '🇺🇸 미국 (United States)' },
  { code: 'JP', name: '🇯🇵 일본 (Japan)' },
  { code: 'GB', name: '🇬🇧 영국 (United Kingdom)' },
  { code: 'FR', name: '🇫🇷 프랑스 (France)' },
  { code: 'DE', name: '🇩🇪 독일 (Germany)' },
  { code: 'CA', name: '🇨🇦 캐나다 (Canada)' },
  { code: 'AU', name: '🇦🇺 호주 (Australia)' },
  { code: 'BR', name: '🇧🇷 브라질 (Brazil)' },
  { code: 'IN', name: '🇮🇳 인도 (India)' },
  { code: 'ID', name: '🇮🇩 인도네시아 (Indonesia)' },
  { code: 'MX', name: '🇲🇽 멕시코 (Mexico)' },
  { code: 'ES', name: '🇪🇸 스페인 (Spain)' },
  { code: 'IT', name: '🇮🇹 이탈리아 (Italy)' },
  { code: 'RU', name: '🇷🇺 러시아 (Russia)' },
  { code: 'TH', name: '🇹🇭 태국 (Thailand)' },
  { code: 'VN', name: '🇻🇳 베트남 (Vietnam)' },
  { code: 'PH', name: '🇵🇭 필리핀 (Philippines)' },
  { code: 'TW', name: '🇹🇼 대만 (Taiwan)' },
  { code: 'HK', name: '🇭🇰 홍콩 (Hong Kong)' },
]

export default function TrendsSection({ token, username }: Props) {
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<MessageType | null>(null)
  const [trends, setTrends] = useState<TrendItem[]>([])
  const [collecting, setCollecting] = useState(false)

  // 필터
  const [filterSource, setFilterSource] = useState<string>('all')
  const [regionCode, setRegionCode] = useState<string>('KR')

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
      const trendsData = await fetchTrends(token)
      setTrends(trendsData)
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handleCollectTrends = async () => {
    if (!regionCode) {
      setMessage({ type: 'error', text: '지역 코드를 선택해주세요.' })
      return
    }

    const regionName = REGION_CODES.find(r => r.code === regionCode)?.name || regionCode
    if (!confirm(`${regionName} 지역의 트렌드를 수집하시겠습니까? (백그라운드 작업, 30초-1분 소요)`)) {
      return
    }

    try {
      setCollecting(true)
      await collectTrends(token, regionCode)
      setMessage({ type: 'success', text: '✅ 트렌드 수집이 완료되었습니다!' })
      
      // 자동 새로고침 (3초 후)
      setTimeout(() => {
        void loadData()
      }, 3000)
    } catch (err) {
      const errorMessage = (err as Error).message
      setMessage({ type: 'error', text: `❌ 트렌드 수집 실패: ${errorMessage}` })
      console.error('트렌드 수집 오류:', err)
    } finally {
      setCollecting(false)
    }
  }

  const filteredTrends = trends.filter((trend) => {
    if (filterSource === 'all') return true
    return trend.source === filterSource
  })

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
      <h2>📈 트렌드 분석</h2>
      <p className="section-description">
        YouTube/TikTok의 실시간 트렌드를 수집하고 분석합니다. (사용자: {username})
      </p>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 트렌드 수집 */}
      <div className="content-card">
        <h3>🔄 트렌드 수집</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>지역 코드 *</label>
            <select
              value={regionCode}
              onChange={(e) => setRegionCode(e.target.value)}
              style={{
                padding: '0.5rem',
                fontSize: '1rem',
                borderRadius: '0.375rem',
                border: '1px solid #ddd',
                backgroundColor: 'white',
                cursor: 'pointer'
              }}
            >
              {REGION_CODES.map((region) => (
                <option key={region.code} value={region.code}>
                  {region.name}
                </option>
              ))}
            </select>
            <small>YouTube 트렌딩 영상을 수집할 국가/지역을 선택하세요</small>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          <button
            className="btn btn-primary"
            onClick={() => void handleCollectTrends()}
            disabled={collecting || !regionCode}
          >
            {collecting ? (
              <>
                <span className="loading-spinner"></span> 수집 중...
              </>
            ) : (
              '🚀 트렌드 수집 시작'
            )}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => void loadData()}
          >
            🔄 새로고침
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="stat-card">
          <div className="stat-label">전체 트렌드</div>
          <div className="stat-value">{trends.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">YouTube</div>
          <div className="stat-value">{trends.filter((t) => t.source === 'youtube').length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">TikTok</div>
          <div className="stat-value">{trends.filter((t) => t.source === 'tiktok').length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">평균 트렌드 점수</div>
          <div className="stat-value">
            {trends.length > 0 
              ? (trends.reduce((sum, t) => sum + t.trend_score, 0) / trends.length).toFixed(1)
              : '0'}
          </div>
        </div>
      </div>

      {/* 필터 */}
      <div className="content-card">
        <h3>🔍 필터</h3>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            className={`btn ${filterSource === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterSource('all')}
          >
            전체
          </button>
          <button
            className={`btn ${filterSource === 'youtube' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterSource('youtube')}
          >
            📺 YouTube
          </button>
          <button
            className={`btn ${filterSource === 'tiktok' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterSource('tiktok')}
          >
            🎵 TikTok
          </button>
        </div>
      </div>

      {/* 트렌드 목록 */}
      <div className="content-card">
        <h3>📋 트렌드 목록 ({filteredTrends.length}개)</h3>
        {filteredTrends.length === 0 ? (
          <p className="empty-state">
            트렌드가 없습니다. 위의 "트렌드 수집 시작" 버튼을 클릭하세요.
          </p>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>소스</th>
                  <th>키워드</th>
                  <th>주제</th>
                  <th>카테고리</th>
                  <th>트렌드 점수</th>
                  <th>조회수</th>
                  <th>영상 수</th>
                  <th>성장률</th>
                  <th>언어</th>
                  <th>지역</th>
                  <th>수집 시각</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrends.map((trend) => (
                  <tr key={trend.id}>
                    <td>
                      <span className="status-badge online">
                        {trend.source === 'youtube' ? '📺 YouTube' : '🎵 TikTok'}
                      </span>
                    </td>
                    <td>
                      <strong>{trend.keyword}</strong>
                    </td>
                    <td>{trend.topic || '-'}</td>
                    <td>{trend.category || '-'}</td>
                    <td>
                      <span style={{ 
                        fontWeight: 'bold',
                        color: trend.trend_score >= 80 ? '#10b981' : trend.trend_score >= 50 ? '#f59e0b' : '#6b7280'
                      }}>
                        {trend.trend_score}
                      </span>
                    </td>
                    <td>{trend.view_count.toLocaleString()}</td>
                    <td>{trend.video_count.toLocaleString()}</td>
                    <td>
                      <span style={{ color: trend.growth_rate > 0 ? '#10b981' : '#ef4444' }}>
                        {trend.growth_rate > 0 ? '+' : ''}{trend.growth_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td>{trend.language}</td>
                    <td>{trend.region}</td>
                    <td>{new Date(trend.collected_at).toLocaleString('ko-KR')}</td>
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
          <li><strong>트렌드 수집:</strong> Celery Worker가 백그라운드에서 YouTube/TikTok API를 호출합니다.</li>
          <li><strong>지역 코드:</strong> KR(한국), US(미국), JP(일본) 등 ISO 2자리 코드를 사용합니다.</li>
          <li><strong>트렌드 점수:</strong> 80+ (매우 높음), 50-79 (높음), 50 미만 (보통)</li>
          <li><strong>스크립트 생성:</strong> 높은 점수의 키워드를 "스크립트" 메뉴에서 활용할 수 있습니다.</li>
        </ul>
      </div>
    </div>
  )
}
