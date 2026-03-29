import { RadioTower } from 'lucide-react'
import type { RealtimeConnectionState } from '../types'

interface RealtimeStatusBadgeProps {
  state: RealtimeConnectionState
  retryAttempt?: number
  liveLabel?: string
  connectingLabel?: string
  reconnectingLabel?: string
  offlineLabel?: string
  compact?: boolean
}

export default function RealtimeStatusBadge({
  state,
  retryAttempt = 0,
  liveLabel = 'Realtime live',
  connectingLabel = 'Connecting live feed',
  reconnectingLabel = 'Reconnecting live feed',
  offlineLabel = 'Realtime offline',
  compact = false,
}: RealtimeStatusBadgeProps) {
  const toneClasses =
    state === 'live'
      ? 'bg-[#0c241b] text-lazarus-normal border-lazarus-normal/15'
      : state === 'connecting' || state === 'reconnecting'
        ? 'bg-[#181e16] text-lazarus-warning border-lazarus-warning/15'
        : 'bg-[#111821] text-lazarus-muted border-white/8'

  const dotClasses =
    state === 'live'
      ? 'bg-lazarus-normal motion-dot-live'
      : state === 'connecting' || state === 'reconnecting'
        ? 'bg-lazarus-warning'
        : 'bg-lazarus-muted'

  const label =
    state === 'live'
      ? liveLabel
      : state === 'connecting'
        ? connectingLabel
        : state === 'reconnecting'
          ? reconnectingLabel
          : offlineLabel

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs font-semibold ${toneClasses} ${
        compact ? '' : 'shadow-[0_12px_28px_rgba(2,6,13,0.24)]'
      }`}
    >
      <RadioTower size={13} strokeWidth={2.1} />
      <span className={`h-2 w-2 rounded-full ${dotClasses}`} aria-hidden="true" />
      <span>{label}</span>
      {state === 'reconnecting' && retryAttempt > 0 && (
        <span className="text-[11px] uppercase tracking-[0.08em] opacity-80">
          Retry {retryAttempt}
        </span>
      )}
    </span>
  )
}
