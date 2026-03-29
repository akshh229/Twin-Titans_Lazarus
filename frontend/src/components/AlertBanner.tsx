import { useAlerts } from '../hooks/useAlerts'
import { AlertOctagon, Activity } from 'lucide-react'

export default function AlertBanner() {
  const { data: alerts, isLoading } = useAlerts()

  if (isLoading || !alerts || alerts.length === 0) return null

  return (
    <div className="alert-banner" aria-live="assertive" role="alert">
      <div className="max-w-7xl mx-auto px-6 py-3.5">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[#ffb4ab] font-bold text-sm tracking-wide bg-[#93000a]/30 px-3 py-1.5 rounded-md ring-1 ring-[#ffb4ab]/20">
            <AlertOctagon size={16} strokeWidth={2.5} />
            CRITICAL ({alerts.length})
          </div>
          <div className="flex-1 flex flex-wrap gap-x-6 gap-y-2">
            {alerts.map((alert) => (
              <div key={alert.id} className="flex items-center gap-2.5">
                <span className="text-lazarus-text font-medium text-sm">
                  {alert.patient_name || 'Unknown'} <span className="text-lazarus-muted font-normal ml-1">({alert.ward || 'N/A'})</span>
                </span>
                <span className="flex items-center gap-1.5 bg-[#0a0e14] px-2.5 py-1 rounded text-xs font-mono text-[#ffb4ab] font-bold ring-1 ring-[#424754]/30">
                  <Activity size={12} />
                  BPM {alert.last_bpm} {alert.last_bpm && alert.last_bpm > 100 ? '\u2191' : '\u2193'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
