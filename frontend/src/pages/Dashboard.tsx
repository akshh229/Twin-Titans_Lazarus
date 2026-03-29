import { usePatients } from '../hooks/usePatients'
import PatientCard from '../components/PatientCard'

export default function Dashboard() {
  const { data: patients, isLoading, error } = usePatients()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lazarus-muted">Loading patients...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card border-lazarus-critical">
        <h2 className="text-lazarus-critical font-semibold mb-2">Connection Error</h2>
        <p className="text-lazarus-muted text-sm">
          Unable to connect to the Lazarus backend. Ensure the server is running at http://localhost:8000
        </p>
      </div>
    )
  }

  if (!patients || patients.length === 0) {
    return (
      <div className="card">
        <h2 className="text-lazarus-text font-semibold mb-2">No Patient Data</h2>
        <p className="text-lazarus-muted text-sm">
          No patients found. Run the seed data generator to populate the system:
        </p>
        <code className="block mt-2 text-xs text-lazarus-info font-mono">
          python seed_data/generate_seeds.py && python seed_data/load_seeds.py
        </code>
      </div>
    )
  }

  const criticalPatients = patients.filter((p) => p.has_active_alert)
  const stablePatients = patients.filter((p) => !p.has_active_alert)

  return (
    <div className="page-entrance">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-lazarus-text">Patient Dashboard</h1>
          <p className="text-sm text-lazarus-muted">
            {patients.length} total | {criticalPatients.length} critical | {stablePatients.length} stable
          </p>
        </div>
      </div>

      {criticalPatients.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-lazarus-critical mb-3 uppercase tracking-wide">
            Critical Patients ({criticalPatients.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {criticalPatients.map((patient, index) => (
              <PatientCard key={patient.patient_id} patient={patient} index={index} />
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="text-sm font-semibold text-lazarus-muted mb-3 uppercase tracking-wide">
          Stable Patients ({stablePatients.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stablePatients.map((patient, index) => (
            <PatientCard
              key={patient.patient_id}
              patient={patient}
              index={criticalPatients.length + index}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
