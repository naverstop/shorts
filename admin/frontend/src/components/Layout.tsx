import type { ReactNode } from 'react'
import './Layout.css'

export type LayoutProps = {
  sidebar: ReactNode
  header: ReactNode
  children: ReactNode
}

export function Layout({ sidebar, header, children }: LayoutProps) {
  return (
    <div className="layout">
      <aside className="layout-sidebar">{sidebar}</aside>
      <div className="layout-main">
        <header className="layout-header">{header}</header>
        <main className="layout-content">{children}</main>
      </div>
    </div>
  )
}
