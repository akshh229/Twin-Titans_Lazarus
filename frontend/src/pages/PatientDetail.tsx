import { useParams, Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { usePatient } from '../hooks/usePatients'
import { useVitals } from '../hooks/useVitals'
import { usePrescriptions } from '../hooks/usePrescriptions'
import { usePatientRealtime } from '../hooks/usePatientRealtime'
import PatientAlertPanel from '../components/PatientAlertPanel'
import RealtimeStatusBadge from '../components/RealtimeStatusBadge'
import TelemetrySimulatorPanel from '../components/TelemetrySimulatorPanel'
import VitalsChart from '../components/VitalsChart'
import PharmacyTable from '../components/PharmacyTable'

export default function PatientDetail() {
  const { patientId } = useParams<{ patientId: string }>()
  const { data: patient, isLoading: patientLoading } = usePatient(patientId || '')
  const { data: vitals, isLoading: vitalsLoading } = useVitals(patientId || '', 24, {
    refetchInterval: false,
  })
  const { data: prescriptions, isLoading: rxLoading } = usePrescriptions(patientId || '')
  const { connectionState, lastMessageAt, retryAttempt } = usePatientRealtime(patientId || '')
  const [isRealtimeFlash, setIsRealtimeFlash] = useState(false)

  useEffect(() => {
    if (!lastMessageAt) {
      return
    }

    setIsRealtimeFlash(true)
    const timeoutId = window.setTimeout(() => setIsRealtimeFlash(false), 900)
    return () => window.clearTimeout(timeoutId)
  }, [lastMessageAt])

  if (patientLoading) {
    return <div className="text-lazarus-muted">Loading patient data...</div>
  }

  if (!patient) {
    return (
      <div className="card">
        <h2 className="text-lazarus-critical font-semibold">Patient Not Found</h2>
        <Link to="/" className="text-lazarus-info text-sm mt-2 inline-block">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="page-entrance">
      <Link to="/" className="inline-block text-lazarus-info text-sm mb-4 transition-transform duration-300 hover:-translate-x-1">
        &larr; Back to Dashboard
      </Link>

      {/* Patient Header */}
      <div className={`card mb-6 ${isRealtimeFlash ? 'live-shell-flash' : ''}`}>
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-lazarus-text">
                {patient.name || `Patient ${patient.patient_raw_id}`}
              </h1>
              {patient.has_active_alert && <span className="badge-critical">Critical</span>}
              <RealtimeStatusBadge
                state={connectionState}
                retryAttempt={retryAttempt}
                liveLabel="Live monitor"
                connectingLabel="Connecting monitor"
                reconnectingLabel="Reconnecting monitor"
                offlineLabel="Monitor offline"
              />
            </div>
            <p className="mt-2 text-sm text-lazarus-muted">
              Continuous patient telemetry with medication decryption and alert monitoring.
            </p>
            <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm text-lazarus-muted sm:flex sm:flex-wrap sm:gap-x-6 sm:gap-y-2">
              <span>Age: {patient.age}</span>
              <span>Ward: {patient.ward}</span>
              <span className="truncate">Raw ID: {patient.patient_raw_id}</span>
              <span>Parity: {patient.parity_flag}</span>
              <span>
                Confidence:{' '}
                {patient.identity_confidence
                  ? `${(patient.identity_confidence * 100).toFixed(0)}%`
                  : 'N/A'}
              </span>
              {lastMessageAt && (
                <span>
                  Last signal:{' '}
                  {new Date(lastMessageAt).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:min-w-[20rem]">
            <div className={`rounded-xl bg-lazarus-surface-low/80 px-4 py-4 text-center ring-1 ring-lazarus-border/30 transition-all duration-500 ${isRealtimeFlash ? 'live-vitals-card' : ''}`}>
              <p className="vitals-label">BPM</p>
              <p
                className={`vitals-value ${
                  patient.last_bpm && (patient.last_bpm < 60 || patient.last_bpm > 100)
                    ? 'text-lazarus-critical'
                    : 'text-lazarus-normal'
                }`}
              >
                {patient.last_bpm ?? '--'}
              </p>
            </div>
            <div className={`rounded-xl bg-lazarus-surface-low/80 px-4 py-4 text-center ring-1 ring-lazarus-border/30 transition-all duration-500 delay-75 ${isRealtimeFlash ? 'live-vitals-card' : ''}`}>
              <p className="vitals-label">SpO2</p>
              <p
                className={`vitals-value ${
                  patient.last_oxygen && patient.last_oxygen < 90
                    ? 'text-lazarus-critical'
                    : 'text-lazarus-normal'
                }`}
              >
                {patient.last_oxygen != null ? `${patient.last_oxygen}%` : '--'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {patientId && <PatientAlertPanel patientId={patientId} />}
      {patientId && (
        <TelemetrySimulatorPanel
          patientId={patientId}
          connectionState={connectionState}
        />
      )}

      {/* Vitals Chart */}
      <div className="mb-6">
        {vitalsLoading ? (
          <div className="card text-lazarus-muted">Loading vitals...</div>
        ) : vitals && vitals.data.length > 0 ? (
          <div className={isRealtimeFlash ? 'live-shell-flash rounded-xl' : ''}>
            <VitalsChart data={vitals.data} title="Vitals Integrity Monitor - 24h" />
          </div>
        ) : (
          <div className="card text-lazarus-muted">No vitals data available for this patient.</div>
        )}
      </div>

      {/* Prescriptions */}
      {rxLoading ? (
        <div className="card text-lazarus-muted">Loading prescriptions...</div>
      ) : (
        <PharmacyTable prescriptions={prescriptions || []} />
      )}
    </div>
  )
}
