import { useState, useEffect } from 'react'
import { fetchTrends, fetchTrendSources, collectTrends, type TrendItem, type TrendSourceItem } from '../services/api'
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
  const [trendSources, setTrendSources] = useState<TrendSourceItem[]>([])
  const [collecting, setCollecting] = useState(false)

  // 필터
  const [filterSource, setFilterSource] = useState<string>('all')
  const [regionCode, setRegionCode] = useState<string>('KR')
  const [selectedSources, setSelectedSources] = useState<string[]>([])

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
      const [trendsData, sourcesData] = await Promise.all([
        fetchTrends(token),
        fetchTrendSources(token),
      ])
      setTrends(trendsData)
      setTrendSources(sourcesData.filter((source) => source.enabled))
      setSelectedSources((prev) => prev.length > 0 ? prev : sourcesData.filter((source) => source.enabled && source.supports_collection).map((source) => source.code))
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const toggleSelectedSource = (sourceCode: string) => {
    setSelectedSources((prev) =>
      prev.includes(sourceCode)
        ? prev.filter((code) => code !== sourceCode)
        : [...prev, sourceCode]
    )
  }

  const handleCollectTrends = async () => {
    if (!regionCode) {
      setMessage({ type: 'error', text: '지역 코드를 선택해주세요.' })
      return
    }

    if (selectedSources.length === 0) {
      setMessage({ type: 'error', text: '수집할 플랫폼을 1개 이상 선택해주세요.' })
      return
    }

    const regionName = REGION_CODES.find(r => r.code === regionCode)?.name || regionCode
    const sourceNames = trendSources
      .filter((source) => selectedSources.includes(source.code))
      .map((source) => `${source.icon} ${source.label}`)
      .join(', ')
    if (!confirm(`${regionName} 지역의 트렌드를 수집하시겠습니까?\n대상: ${sourceNames}\n(백그라운드 작업, 30초-1분 소요)`)) {
      return
    }

    try {
      setCollecting(true)
      await collectTrends(token, regionCode, selectedSources)
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

  const getSourceLabel = (source: string) => {
    const found = trendSources.find((item) => item.code === source)
    return found ? `${found.icon} ${found.label}` : source
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
              title="지역 코드 선택"
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
          <div className="form-group">
            <label>수집 플랫폼 *</label>
            <div>
              {trendSources.filter((source) => source.supports_collection).map((source) => (
                <label key={source.code} className="checkbox-label" style={{ marginBottom: '0.5rem' }}>
                  <input
                    type="checkbox"
                    checked={selectedSources.includes(source.code)}
                    onChange={() => toggleSelectedSource(source.code)}
                  />
                  <span>{source.icon} {source.label}</span>
                </label>
              ))}
            </div>
            <small>체크된 플랫폼을 한 번에 수집합니다</small>
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
        {trendSources.map((source) => (
          <div className="stat-card" key={source.code}>
            <div className="stat-label">{source.icon} {source.label}</div>
            <div className="stat-value">{trends.filter((t) => t.source === source.code).length}</div>
          </div>
        ))}
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
          {trendSources.map((source) => (
            <button
              key={source.code}
              className={`btn ${filterSource === source.code ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilterSource(source.code)}
            >
              {source.icon} {source.label}
            </button>
          ))}
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
                  <th className="text-right">트렌드 점수</th>
                  <th className="text-right">연관 조회수</th>
                  <th className="text-right">연관 영상 수</th>
                  <th className="text-right">성장률</th>
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
                        {getSourceLabel(trend.source)}
                      </span>
                    </td>
                    <td>
                      <strong>{trend.keyword}</strong>
                    </td>
                    <td>{trend.topic || '-'}</td>
                    <td>{trend.category || '-'}</td>
                    <td className="text-right">
                      <span style={{ 
                        fontWeight: 'bold',
                        color: trend.trend_score >= 80 ? '#10b981' : trend.trend_score >= 50 ? '#f59e0b' : '#6b7280'
                      }}>
                        {trend.trend_score}
                      </span>
                    </td>
                    <td className="text-right">{trend.view_count.toLocaleString()}</td>
                    <td className="text-right">{trend.video_count.toLocaleString()}</td>
                    <td className="text-right">
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
          <li><strong>트렌드 수집:</strong> 선택한 플랫폼별로 YouTube, YouTube Shorts, TikTok 트렌드를 수집합니다.</li>
          <li><strong>지역 코드:</strong> KR(한국), US(미국), JP(일본) 등 ISO 2자리 코드를 사용합니다.</li>
          <li><strong>트렌드 점수:</strong> 80+ (매우 높음), 50-79 (높음), 50 미만 (보통)</li>
          <li><strong>YouTube Shorts:</strong> 현재는 YouTube 인기 영상 중 60초 이하 영상을 Shorts 후보로 분류합니다.</li>
          <li><strong>스크립트 생성:</strong> 높은 점수의 키워드를 "스크립트" 메뉴에서 활용할 수 있습니다.</li>
        </ul>
      </div>
    </div>
  )
}
