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
      <header className="border-b border-white/6 bg-[#0a1119]/86 px-4 py-4 backdrop-blur-xl sm:px-6">
        <div className="mx-auto grid max-w-7xl gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <Link to="/" className="flex min-w-0 items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-[1.15rem] border border-white/10 bg-[linear-gradient(180deg,rgba(138,168,255,0.26),rgba(34,45,60,0.84))] shadow-[0_16px_36px_rgba(7,13,24,0.36)]">
                <span className="font-mono text-lg font-semibold text-lazarus-text">L</span>
              </div>
              <div className="min-w-0">
                <p className="display-kicker">Forensic telemetry board</p>
                <h1 className="font-display text-[2rem] leading-none tracking-[-0.03em] text-lazarus-text">
                  Lazarus
                </h1>
                <p className="mt-1 text-sm text-lazarus-muted">
                  Medical forensic recovery
                </p>
              </div>
            </Link>

            <div className="hidden lg:block">
              <p className="text-sm font-medium text-lazarus-text/88">
                St. Jude&apos;s Research Hospital
              </p>
              <p className="mt-1 text-xs uppercase tracking-[0.24em] text-lazarus-muted/70">
                Critical care observability workspace
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 sm:justify-end">
            <RealtimeStatusBadge
              state={realtimeState}
              retryAttempt={realtimeRetryAttempt}
              compact
            />
            <div className="inline-flex items-center gap-2 rounded-full border border-white/7 bg-[#0e1620]/90 px-3 py-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
              <div
                className={`h-2.5 w-2.5 rounded-full ${statusTone} ${isError ? '' : 'animate-pulse'}`}
                aria-hidden="true"
              />
              <span className="text-xs font-semibold text-lazarus-text">{systemStatus}</span>
              {health?.version && (
                <span className="font-mono text-[11px] text-lazarus-muted">v{health.version}</span>
              )}
            </div>
          </div>
        </div>
      </header>

      <AlertBanner />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:py-10">
        {children}
      </main>
    </div>
  )
}
