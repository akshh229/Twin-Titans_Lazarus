import { useParams, Link } from 'react-router-dom'
import { usePatient } from '../hooks/usePatients'
import { useVitals } from '../hooks/useVitals'
import { usePrescriptions } from '../hooks/usePrescriptions'
import VitalsChart from '../components/VitalsChart'
import PharmacyTable from '../components/PharmacyTable'

export default function PatientDetail() {
  const { patientId } = useParams<{ patientId: string }>()
  const { data: patient, isLoading: patientLoading } = usePatient(patientId || '')
  const { data: vitals, isLoading: vitalsLoading } = useVitals(patientId || '')
  const { data: prescriptions, isLoading: rxLoading } = usePrescriptions(patientId || '')

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
    <div>
      <Link to="/" className="text-lazarus-info text-sm mb-4 inline-block">
        &larr; Back to Dashboard
      </Link>

      {/* Patient Header */}
      <div className="card mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-lazarus-text">
              {patient.name || `Patient ${patient.patient_raw_id}`}
              {patient.has_active_alert && <span className="ml-2 badge-critical">CRITICAL</span>}
            </h1>
            <div className="flex gap-6 mt-2 text-sm text-lazarus-muted">
              <span>Age: {patient.age}</span>
              <span>Ward: {patient.ward}</span>
              <span>Raw ID: {patient.patient_raw_id}</span>
              <span>Parity: {patient.parity_flag}</span>
              <span>Confidence: {patient.identity_confidence ? `${(patient.identity_confidence * 100).toFixed(0)}%` : 'N/A'}</span>
            </div>
          </div>
          <div className="flex gap-6">
            <div className="text-center">
              <p className="vitals-label">BPM</p>
              <p className={`vitals-value ${patient.last_bpm && (patient.last_bpm < 60 || patient.last_bpm > 100) ? 'text-lazarus-critical' : 'text-lazarus-normal'}`}>
                {patient.last_bpm ?? '--'}
              </p>
            </div>
            <div className="text-center">
              <p className="vitals-label">SpO2</p>
              <p className={`vitals-value ${patient.last_oxygen && patient.last_oxygen < 90 ? 'text-lazarus-critical' : 'text-lazarus-normal'}`}>
                {patient.last_oxygen != null ? `${patient.last_oxygen}%` : '--'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Vitals Chart */}
      <div className="mb-6">
        {vitalsLoading ? (
          <div className="card text-lazarus-muted">Loading vitals...</div>
        ) : vitals && vitals.data.length > 0 ? (
          <VitalsChart data={vitals.data} title="Vitals Integrity Monitor - 24h" />
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
