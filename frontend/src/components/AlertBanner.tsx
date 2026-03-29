import { Link } from 'react-router-dom'
import { useAlerts } from '../hooks/useAlerts'
import { AlertOctagon, Activity } from 'lucide-react'

export default function AlertBanner() {
  const { data: alerts, isLoading } = useAlerts()

  if (isLoading || !alerts || alerts.length === 0) return null

  return (
    <div className="alert-banner" aria-live="polite" role="status">
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="critical-chip flex w-fit items-center gap-2 rounded-full border border-[#ffd1cb]/14 bg-[#361417]/85 px-3.5 py-1.5 text-sm font-bold tracking-wide text-[#ffd1cb] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
            <AlertOctagon size={16} strokeWidth={2.5} />
            CRITICAL ({alerts.length})
          </div>
          <div className="flex-1">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#ffb7b0]/70">
              Active escalation queue
            </p>
            <div className="flex flex-wrap gap-x-6 gap-y-2">
            {alerts.map((alert, index) => (
              <Link
                key={alert.id}
                to={`/patient/${alert.patient_id}`}
                className="alert-item flex items-center gap-2.5 rounded-full px-3 py-2 outline-none transition-colors hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-lazarus-accent"
                style={{ animationDelay: `${index * 60}ms` }}
              >
                <span className="text-sm font-medium text-lazarus-text">
                  {alert.patient_name || 'Unknown'} <span className="ml-1 font-normal text-lazarus-muted">({alert.ward || 'N/A'})</span>
                </span>
                <span className="signal-pill flex items-center gap-1.5 rounded-full bg-[#0a0f15] px-2.5 py-1 text-xs font-mono font-bold text-[#ffd1cb] ring-1 ring-white/8">
                  <Activity size={12} />
                  BPM {alert.last_bpm ?? '--'} {alert.last_bpm == null ? '' : alert.last_bpm > 100 ? '\u2191' : '\u2193'}
                </span>
              </Link>
            ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
