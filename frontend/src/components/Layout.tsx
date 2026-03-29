import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import AlertBanner from './AlertBanner'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-lazarus-bg">
      <header className="bg-lazarus-surface border-b border-lazarus-border px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-lazarus-accent rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">L</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-lazarus-text">Lazarus</h1>
              <p className="text-xs text-lazarus-muted">Medical Forensic Recovery</p>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-xs text-lazarus-muted">St. Jude's Research Hospital</span>
            <div className="w-2 h-2 bg-lazarus-normal rounded-full animate-pulse" title="Connected" />
          </div>
        </div>
      </header>

      <AlertBanner />

      <main className="max-w-7xl mx-auto px-6 py-6">
        {children}
      </main>
    </div>
  )
}
