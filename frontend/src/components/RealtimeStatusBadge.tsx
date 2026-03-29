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
      ? 'bg-[#00311f] text-lazarus-normal ring-lazarus-normal/20'
      : state === 'connecting' || state === 'reconnecting'
        ? 'bg-lazarus-surface-low text-lazarus-warning ring-lazarus-warning/20'
        : 'bg-lazarus-surface-low text-lazarus-muted ring-lazarus-border/40'

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
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ring-1 ${toneClasses} ${
        compact ? '' : 'shadow-[0_8px_24px_rgba(3,7,18,0.18)]'
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
