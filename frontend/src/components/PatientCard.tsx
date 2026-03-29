import { Link } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react'
import type { Patient } from '../types'

interface PatientCardProps {
  patient: Patient
  isSelected?: boolean
}

export default function PatientCard({ patient, isSelected }: PatientCardProps) {
  const bpmStatus = patient.last_bpm
    ? patient.last_bpm >= 60 && patient.last_bpm <= 100
      ? 'normal'
      : 'critical'
    : 'unknown'

  return (
    <Link to={`/patient/${patient.patient_id}`}>
      <div className={`card group cursor-pointer ${patient.has_active_alert ? 'card-critical' : ''} ${isSelected ? 'ring-lazarus-accent/50 bg-lazarus-surface-high/60' : 'hover:bg-lazarus-surface-high/40'}`}>
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-semibold text-lg text-lazarus-text tracking-tight flex items-center gap-2">
              {patient.name || `Patient ${patient.patient_raw_id}`}
            </h3>
            <p className="text-sm font-medium text-lazarus-muted mt-0.5">
              Age: {patient.age || 'N/A'} <span className="mx-1.5 opacity-40">•</span> Ward: {patient.ward || 'N/A'}
            </p>
          </div>
          
          {bpmStatus === 'normal' && (
            <span className="badge-normal">
              <CheckCircle2 size={14} strokeWidth={2.5} /> Stable
            </span>
          )}
          {bpmStatus === 'critical' && (
            <span className="badge-critical">
              <AlertOctagon size={14} strokeWidth={2.5} /> Critical
            </span>
          )}
          {bpmStatus === 'unknown' && (
            <span className="badge-warning">
              <AlertTriangle size={14} strokeWidth={2.5} /> No Data
            </span>
          )}
        </div>

        <div className="flex gap-10">
          <div className="flex flex-col gap-1">
            <p className="vitals-label">BPM</p>
            <p className={`vitals-value ${bpmStatus === 'critical' ? 'text-[#ffb4ab]' : 'text-lazarus-text'}`}>
              {patient.last_bpm ?? '--'}
            </p>
          </div>
          <div className="flex flex-col gap-1">
            <p className="vitals-label">SpO2</p>
            <p className={`vitals-value ${patient.last_oxygen && patient.last_oxygen < 90 ? 'text-[#ffb4ab]' : 'text-lazarus-text'}`}>
              {patient.last_oxygen != null ? `${patient.last_oxygen}%` : '--'}
            </p>
          </div>
        </div>

        <div className="mt-6 flex items-center gap-3 text-[0.7rem] font-semibold tracking-wider uppercase text-lazarus-muted/70">
          <span className="bg-[#0a0e14] px-2 py-1 rounded-md ring-1 ring-[#424754]/20">ID: {patient.patient_raw_id}</span>
          <span className="bg-[#0a0e14] px-2 py-1 rounded-md ring-1 ring-[#424754]/20">Parity: {patient.parity_flag}</span>
          <span className="bg-[#0a0e14] px-2 py-1 rounded-md ring-1 ring-[#424754]/20">Rx: {patient.prescription_count}</span>
        </div>
      </div>
    </Link>
  )
}
