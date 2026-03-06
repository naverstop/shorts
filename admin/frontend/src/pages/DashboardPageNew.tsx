import { useState, useEffect } from 'react'
import { Layout } from '../components/Layout'
import { Sidebar } from '../components/Sidebar'
import { DashboardOverview } from '../components/DashboardOverview'
import { AgentsSection } from '../components/AgentsSection'
import { JobsSection } from '../components/JobsSection'
import PlatformsManagementSection from '../components/PlatformsManagementSection'
import TrendsSection from '../components/TrendsSection'
import ScriptsSection from '../components/ScriptsSection'
import { SimCardsSection } from '../components/SimCardsSection'
import { fetchHealth, fetchAgentStats, type HealthResponse, type AgentStatsResponse } from '../services/api'
import './DashboardPageNew.css'

type DashboardPageNewProps = {
  username: string
  token: string
  onLogout: () => void
}

export function DashboardPageNew({ username, token, onLogout }: DashboardPageNewProps) {
  const [activeMenu, setActiveMenu] = useState('home')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [agentStats, setAgentStats] = useState<AgentStatsResponse | null>(null)

  // 시스템 상태 주기적으로 업데이트 (10초마다)
  useEffect(() => {
    const loadSystemStatus = async () => {
      try {
        const [healthData, agentData] = await Promise.all([
          fetchHealth(),
          fetchAgentStats(token),
        ])
        setHealth(healthData)
        setAgentStats(agentData)
      } catch (error) {
        console.error('Failed to load system status:', error)
      }
    }

    void loadSystemStatus()
    const interval = setInterval(() => {
      void loadSystemStatus()
    }, 10000) // 10초마다 업데이트

    return () => clearInterval(interval)
  }, [token])

  const handleMenuChange = (menuId: string) => {
    setActiveMenu(menuId)
  }

  const handleRefresh = () => {
    window.location.reload()
  }

  // Render content based on active menu
  const renderContent = () => {
    switch (activeMenu) {
      case 'home':
        return <DashboardOverview token={token} />
      
      case 'sims':
        return <SimCardsSection token={token} />
      
      case 'agents':
        return <AgentsSection token={token} username={username} />
      
      case 'jobs':
        return <JobsSection token={token} />
      
      case 'platforms':
        return <PlatformsManagementSection token={token} />
      
      case 'trends':
        return <TrendsSection token={token} username={username} />
      
      case 'scripts':
        return <ScriptsSection token={token} username={username} />
      
      default:
        return <DashboardOverview token={token} />
    }
  }

  const sidebar = (
    <Sidebar
      activeMenu={activeMenu}
      onMenuChange={handleMenuChange}
      username={username}
    />
  )

  const header = (
    <div className="header-content">
      <div className="header-left">
        <button className="mobile-menu-btn" onClick={() => {}}>
          ☰
        </button>
        <div className="breadcrumb">
          <span>관리자</span>
          <span className="separator">{' > '}</span>
          <span className="current">{getMenuLabel(activeMenu)}</span>
        </div>
      </div>
      <div className="header-right">
        <div className="system-status">
          <div 
            className={`status-item ${health?.status === 'healthy' ? 'healthy' : 'unhealthy'}`}
            title={`전체 상태: ${health?.status || 'unknown'}`}
          >
            <span className="status-icon">{health?.status === 'healthy' ? '✅' : '⚠️'}</span>
            <span className="status-label">서버</span>
          </div>
          <div 
            className={`status-item ${health?.database === 'connected' ? 'healthy' : 'unhealthy'}`}
            title={`Database: ${health?.database || 'unknown'}`}
          >
            <span className="status-icon">🗄️</span>
            <span className="status-label">DB</span>
          </div>
          <div 
            className={`status-item ${health?.redis === 'connected' ? 'healthy' : 'unhealthy'}`}
            title={`Redis: ${health?.redis || 'unknown'}`}
          >
            <span className="status-icon">⚡</span>
            <span className="status-label">Redis</span>
          </div>
          <div 
            className={`status-item ${health?.services?.api === 'running' ? 'healthy' : 'unhealthy'}`}
            title={`API: ${health?.services?.api || 'unknown'}`}
          >
            <span className="status-icon">🔌</span>
            <span className="status-label">API</span>
          </div>
          <div 
            className="status-item agent-status"
            title={`Agent: ${agentStats?.online_count || 0}개 온라인 / ${agentStats?.total || 0}개 등록`}
          >
            <span className="status-icon">🤖</span>
            <span className="status-label">Agent</span>
            <span className="agent-count">{agentStats?.online_count || 0}/{agentStats?.total || 0}</span>
          </div>
          <div 
            className={`status-item service-status ${health?.status === 'healthy' ? 'healthy' : 'unhealthy'}`}
            title={`서비스 가용여부: ${health?.status === 'healthy' ? 'ON' : 'OFF'}`}
          >
            <span className="status-label">서비스</span>
            <span className="service-badge">{health?.status === 'healthy' ? 'ON' : 'OFF'}</span>
          </div>
        </div>
        <button className="header-btn" onClick={handleRefresh} title="새로고침">
          ↻
        </button>
        <button className="header-btn logout-btn" onClick={onLogout}>
          로그아웃
        </button>
      </div>
    </div>
  )

  return (
    <Layout sidebar={sidebar} header={header}>
      {renderContent()}
    </Layout>
  )
}

function getMenuLabel(menuId: string): string {
  const labels: Record<string, string> = {
    home: '대시보드',
    sims: 'SIM 카드',
    agents: 'Agent 관리',
    jobs: 'Job 관리',
    platforms: '플랫폼 정보',
    trends: '트렌드 관리',
    scripts: '스크립트 관리',
  }
  return labels[menuId] || '대시보드'
}
