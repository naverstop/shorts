import { useState, useEffect } from 'react'
import { 
  fetchScripts, 
  fetchTrends, 
  generateScript,
  type ScriptItem,
  type TrendItem 
} from '../services/api'
import './SectionStyles.css'

type MessageType = { type: 'success' | 'error'; text: string }

interface Props {
  token: string
  username: string
}

export default function ScriptsSection({ token, username }: Props) {
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<MessageType | null>(null)
  const [scripts, setScripts] = useState<ScriptItem[]>([])
  const [trends, setTrends] = useState<TrendItem[]>([])
  const [generating, setGenerating] = useState(false)

  // 생성 폼
  const [topic, setTopic] = useState('')
  const [trendId, setTrendId] = useState<number | null>(null)
  const [targetAudience, setTargetAudience] = useState('10-30대')
  const [platform, setPlatform] = useState('youtube')
  const [language, setLanguage] = useState('ko')
  const [duration, setDuration] = useState(60)

  // 선택된 스크립트 (상세보기)
  const [selectedScript, setSelectedScript] = useState<ScriptItem | null>(null)

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
      const [scriptsData, trendsData] = await Promise.all([
        fetchScripts(token),
        fetchTrends(token),
      ])
      setScripts(scriptsData)
      setTrends(trendsData.slice(0, 20)) // 상위 20개만
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateScript = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!topic.trim()) {
      setMessage({ type: 'error', text: '주제를 입력해주세요.' })
      return
    }

    if (!confirm('AI 스크립트를 생성하시겠습니까? (AI API 키 필요, 30초-1분 소요)')) {
      return
    }

    try {
      setGenerating(true)
      await generateScript(token, {
        topic: topic.trim(),
        trend_id: trendId ?? undefined,
        target_audience: targetAudience,
        platform,
        language,
        duration,
      })
      setMessage({ type: 'success', text: '스크립트 생성이 완료되었습니다.' })
      
      // 폼 초기화
      setTopic('')
      setTrendId(null)
      
      // 목록 새로고침
      await loadData()
    } catch (err) {
      setMessage({ type: 'error', text: (err as Error).message })
    } finally {
      setGenerating(false)
    }
  }

  const handleSelectTrend = (trend: TrendItem) => {
    setTopic(trend.keyword)
    setTrendId(trend.id)
    setMessage({ type: 'success', text: `트렌드 "${trend.keyword}" 선택됨` })
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
      <h2>📝 AI 스크립트 생성</h2>
      <p className="section-description">
        트렌드 기반 AI 스크립트를 생성하고 관리합니다. (사용자: {username})
      </p>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* 통계 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="stat-card">
          <div className="stat-label">전체 스크립트</div>
          <div className="stat-value">{scripts.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">승인됨</div>
          <div className="stat-value">{scripts.filter((s) => s.is_approved).length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">평균 품질 점수</div>
          <div className="stat-value">
            {scripts.length > 0
              ? (scripts.reduce((sum, s) => sum + s.quality_score, 0) / scripts.length).toFixed(1)
              : '0'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">평균 바이럴 점수</div>
          <div className="stat-value">
            {scripts.length > 0
              ? (scripts.reduce((sum, s) => sum + s.viral_potential, 0) / scripts.length).toFixed(1)
              : '0'}
          </div>
        </div>
      </div>

      {/* 스크립트 생성 폼 */}
      <div className="content-card">
        <h3>✨ 새 스크립트 생성</h3>
        <form onSubmit={(e) => void handleGenerateScript(e)}>
          <div className="form-grid">
            <div className="form-group">
              <label>주제 *</label>
              <input
                type="text"
                placeholder="예: 다이어트 팁, 요리 레시피"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>타겟 청중</label>
              <input
                type="text"
                placeholder="예: 10-30대"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>플랫폼</label>
              <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
                <option value="youtube">YouTube Shorts</option>
                <option value="tiktok">TikTok</option>
                <option value="instagram">Instagram Reels</option>
              </select>
            </div>

            <div className="form-group">
              <label>언어</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="ko">한국어</option>
                <option value="en">English</option>
                <option value="ja">日本語</option>
              </select>
            </div>

            <div className="form-group">
              <label>영상 길이 (초)</label>
              <input
                type="number"
                min={15}
                max={180}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={generating || !topic.trim()}
            style={{ marginTop: '1rem' }}
          >
            {generating ? (
              <>
                <span className="loading-spinner"></span> 생성 중...
              </>
            ) : (
              '🚀 AI 스크립트 생성'
            )}
          </button>
        </form>
      </div>

      {/* 트렌드 키워드 선택 */}
      {trends.length > 0 && (
        <div className="content-card">
          <h3>🔥 트렌드 키워드 선택</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {trends.slice(0, 15).map((trend) => (
              <button
                key={trend.id}
                className="btn btn-secondary"
                onClick={() => handleSelectTrend(trend)}
                style={{ fontSize: '0.85rem' }}
              >
                {trend.source === 'youtube' ? '📺' : '🎵'} {trend.keyword}
                <span style={{ marginLeft: '0.5rem', opacity: 0.7 }}>
                  ({trend.trend_score})
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 스크립트 목록 */}
      <div className="content-card">
        <h3>📋 생성된 스크립트 ({scripts.length}개)</h3>
        {scripts.length === 0 ? (
          <p className="empty-state">
            생성된 스크립트가 없습니다. 위의 폼에서 새 스크립트를 생성하세요.
          </p>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>제목</th>
                  <th>언어</th>
                  <th>품질 점수</th>
                  <th>바이럴 점수</th>
                  <th>사용 횟수</th>
                  <th>승인</th>
                  <th>AI 모델</th>
                  <th>생성일</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {scripts.map((script) => (
                  <tr key={script.id}>
                    <td>{script.id}</td>
                    <td>
                      <strong>{script.title}</strong>
                    </td>
                    <td>{script.language.toUpperCase()}</td>
                    <td>
                      <span style={{ 
                        fontWeight: 'bold',
                        color: script.quality_score >= 80 ? '#10b981' : script.quality_score >= 50 ? '#f59e0b' : '#6b7280'
                      }}>
                        {script.quality_score}
                      </span>
                    </td>
                    <td>
                      <span style={{ 
                        fontWeight: 'bold',
                        color: script.viral_potential >= 80 ? '#10b981' : script.viral_potential >= 50 ? '#f59e0b' : '#6b7280'
                      }}>
                        {script.viral_potential}
                      </span>
                    </td>
                    <td>{script.used_count}</td>
                    <td>
                      {script.is_approved ? (
                        <span className="status-badge online">✅ 승인</span>
                      ) : (
                        <span className="status-badge offline">⏳ 대기</span>
                      )}
                    </td>
                    <td>{script.ai_model || '-'}</td>
                    <td>{new Date(script.created_at).toLocaleString('ko-KR')}</td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        onClick={() => setSelectedScript(script)}
                        style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                      >
                        📄 상세
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 스크립트 상세보기 모달 */}
      {selectedScript && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem',
          }}
          onClick={() => setSelectedScript(null)}
        >
          <div 
            className="content-card"
            style={{
              maxWidth: '800px',
              maxHeight: '80vh',
              overflow: 'auto',
              position: 'relative',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedScript(null)}
              style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                background: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
              }}
            >
              ✕ 닫기
            </button>

            <h3>📄 스크립트 상세</h3>
            <div style={{ marginTop: '1rem' }}>
              <h4>{selectedScript.title}</h4>
              <div style={{ marginTop: '1rem' }}>
                <strong>Hook (훅):</strong>
                <p style={{ 
                  background: '#f8f9fa', 
                  padding: '1rem', 
                  borderRadius: '4px',
                  marginTop: '0.5rem',
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedScript.hook || '(없음)'}
                </p>
              </div>
              <div style={{ marginTop: '1rem' }}>
                <strong>Body (본문):</strong>
                <p style={{ 
                  background: '#f8f9fa', 
                  padding: '1rem', 
                  borderRadius: '4px',
                  marginTop: '0.5rem',
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedScript.body || '(없음)'}
                </p>
              </div>
              <div style={{ marginTop: '1rem' }}>
                <strong>CTA (콜투액션):</strong>
                <p style={{ 
                  background: '#f8f9fa', 
                  padding: '1rem', 
                  borderRadius: '4px',
                  marginTop: '0.5rem',
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedScript.cta || '(없음)'}
                </p>
              </div>
              <div style={{ marginTop: '1rem' }}>
                <strong>전체 내용:</strong>
                <p style={{ 
                  background: '#f8f9fa', 
                  padding: '1rem', 
                  borderRadius: '4px',
                  marginTop: '0.5rem',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '300px',
                  overflow: 'auto'
                }}>
                  {selectedScript.content}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 사용 가이드 */}
      <div className="content-card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <h3>💡 사용 가이드</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li><strong>AI 모델:</strong> Claude/OpenAI API 키 설정 필요 (Backend .env 파일)</li>
          <li><strong>트렌드 활용:</strong> 높은 트렌드 점수 키워드를 선택하면 바이럴 가능성 증가</li>
          <li><strong>Hook-Body-CTA:</strong> 영상 구조에 최적화된 3단계 스크립트</li>
          <li><strong>Job 생성:</strong> 생성된 스크립트를 복사하여 "Job 관리"에서 영상 제작</li>
        </ul>
      </div>
    </div>
  )
}
