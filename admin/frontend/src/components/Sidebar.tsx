import { useState } from 'react'
import './Sidebar.css'

export type MenuItem = {
  id: string
  label: string
  icon: string
  badge?: number
}

export type SidebarProps = {
  activeMenu: string
  onMenuChange: (menuId: string) => void
  username: string
}

export function Sidebar({ activeMenu, onMenuChange, username }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  const menuItems: MenuItem[] = [
    { id: 'home', label: '홈', icon: '🏠' },
    { id: 'sims', label: 'SIM 카드', icon: '📱' },
    { id: 'platforms', label: '플랫폼 정보', icon: '🌐' },
    { id: 'trends', label: '트렌드 관리', icon: '📈' },
    { id: 'scripts', label: '스크립트 관리', icon: '📝' },
    { id: 'jobs', label: 'Job 관리', icon: '📋' },
    { id: 'agents', label: 'Agent 관리', icon: '🤖' },
  ]

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Logo & User */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="logo-icon">🎬</span>
          {!collapsed && <span className="logo-text">Shorts Admin</span>}
        </div>
        <button
          className="sidebar-toggle"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? '펼치기' : '접기'}
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>

      {/* User Info */}
      {!collapsed && (
        <div className="sidebar-user">
          <div className="user-avatar">👤</div>
          <div className="user-info">
            <div className="user-name">{username}</div>
            <div className="user-role">관리자</div>
          </div>
        </div>
      )}

      {/* Navigation Menu */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeMenu === item.id ? 'active' : ''}`}
            onClick={() => onMenuChange(item.id)}
            title={collapsed ? item.label : undefined}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && <span className="nav-label">{item.label}</span>}
            {!collapsed && item.badge !== undefined && (
              <span className="nav-badge">{item.badge}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="sidebar-footer">
          <div className="sidebar-version">v1.0.0</div>
        </div>
      )}
    </div>
  )
}
