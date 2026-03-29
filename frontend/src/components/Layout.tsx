import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import AlertBanner from './AlertBanner'
import RealtimeStatusBadge from './RealtimeStatusBadge'
import { useHealth } from '../hooks/useHealth'
import { useOverviewRealtime } from '../hooks/useOverviewRealtime'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { connectionState: realtimeState, retryAttempt: realtimeRetryAttempt } =
    useOverviewRealtime()
  const { data: health, isLoading, isError } = useHealth()
  const systemStatus = isError ? 'API offline' : isLoading ? 'Checking API' : 'API healthy'
  const statusTone = isError ? 'bg-lazarus-critical' : 'bg-lazarus-normal'

  return (
    <div className="min-h-screen bg-lazarus-bg">
      <header className="bg-lazarus-surface border-b border-lazarus-border px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-lazarus-accent rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">L</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-lazarus-text">Lazarus</h1>
              <p className="text-xs text-lazarus-muted">Medical Forensic Recovery</p>
            </div>
          </Link>
          <div className="flex flex-wrap items-center gap-3 sm:justify-end">
            <span className="text-xs text-lazarus-muted">St. Jude&apos;s Research Hospital</span>
            <RealtimeStatusBadge
              state={realtimeState}
              retryAttempt={realtimeRetryAttempt}
              compact
            />
            <div className="flex items-center gap-2 rounded-full bg-lazarus-surface-low px-3 py-1.5 ring-1 ring-lazarus-border/40">
              <div
                className={`h-2.5 w-2.5 rounded-full ${statusTone} ${isError ? '' : 'animate-pulse'}`}
                aria-hidden="true"
              />
              <span className="text-xs font-medium text-lazarus-text">{systemStatus}</span>
              {health?.version && (
                <span className="text-[11px] text-lazarus-muted">v{health.version}</span>
              )}
            </div>
          </div>
        </div>
      </header>

      <AlertBanner />

      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6">
        {children}
      </main>
    </div>
  )
}
