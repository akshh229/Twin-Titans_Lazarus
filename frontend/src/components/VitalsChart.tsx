import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea, Legend } from 'recharts'
import type { VitalsDataPoint } from '../types'

interface VitalsChartProps {
  data: VitalsDataPoint[]
  title?: string
  showBpm?: boolean
  showOxygen?: boolean
}

export default function VitalsChart({ data, title, showBpm = true, showOxygen = true }: VitalsChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }))
  const latestPoint = chartData[chartData.length - 1]

  return (
    <div className="card chart-shell">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          {title && <h3 className="text-sm font-semibold text-lazarus-text">{title}</h3>}
          <p className="mt-1 text-xs text-lazarus-muted">
            Streaming telemetry with animated deltas for the most recent sample.
          </p>
        </div>
        {latestPoint && (
          <div className="signal-pill rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-muted">
            Latest sample {latestPoint.time}
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#424754" strokeOpacity={0.4} vertical={false} />
          <XAxis
            dataKey="time"
            stroke="#94a3b8"
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          {showBpm && (
            <YAxis
              yAxisId="bpm"
              domain={[40, 160]}
              stroke="#94a3b8"
              tick={{ fontSize: 11 }}
              label={{ value: 'BPM', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
            />
          )}
          {showOxygen && (
            <YAxis
              yAxisId="oxygen"
              orientation="right"
              domain={[85, 100]}
              stroke="#94a3b8"
              tick={{ fontSize: 11 }}
              label={{ value: 'SpO2%', angle: 90, position: 'insideRight', fill: '#94a3b8', fontSize: 11 }}
            />
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(28, 32, 38, 0.9)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(66, 71, 84, 0.3)',
              borderRadius: '8px',
              color: '#e2e8f0',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)'
            }}
          />
          <Legend />

          {/* BPM safe zone */}
          {showBpm && (
            <>
              <ReferenceArea yAxisId="bpm" y1={60} y2={100} fill="#10b981" fillOpacity={0.1} />
              <ReferenceLine yAxisId="bpm" y={60} stroke="#10b981" strokeDasharray="5 5" strokeOpacity={0.5} />
              <ReferenceLine yAxisId="bpm" y={100} stroke="#10b981" strokeDasharray="5 5" strokeOpacity={0.5} />
            </>
          )}

          {/* SpO2 safe zone */}
          {showOxygen && (
            <ReferenceArea yAxisId="oxygen" y1={95} y2={100} fill="#3b82f6" fillOpacity={0.1} />
          )}

          {showBpm && (
            <Line
              yAxisId="bpm"
              type="monotone"
              dataKey="bpm"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0, fill: '#ffb4ab' }}
              isAnimationActive
              animationDuration={450}
              animationEasing="ease-out"
              name="BPM"
            />
          )}
          {showOxygen && (
            <Line
              yAxisId="oxygen"
              type="monotone"
              dataKey="oxygen"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0, fill: '#93c5fd' }}
              isAnimationActive
              animationDuration={450}
              animationEasing="ease-out"
              name="SpO2"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
