import type { Prescription } from '../types'

interface PharmacyTableProps {
  prescriptions: Prescription[]
}

export default function PharmacyTable({ prescriptions }: PharmacyTableProps) {
  if (!prescriptions || prescriptions.length === 0) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-lazarus-text mb-4">Pharmacy Portal</h3>
        <p className="text-lazarus-muted text-sm">No prescriptions found.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-lazarus-text mb-4">Pharmacy Portal - Medication Decryption</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-lazarus-muted text-left border-b border-[#424754]/30">
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Time</th>
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Encrypted</th>
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Decrypted</th>
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Dose</th>
              <th className="pb-3 font-semibold tracking-wider uppercase text-xs">Route</th>
            </tr>
          </thead>
          <tbody>
            {prescriptions.map((rx) => (
              <tr key={rx.id} className="border-b border-[#424754]/15 hover:bg-[#31353c]/40 transition-colors">
                <td className="py-3 pr-4 font-mono text-xs text-lazarus-muted">
                  {new Date(rx.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </td>
                <td className="py-3 pr-4 font-mono text-lazarus-warning/80 tracking-wide text-xs">
                  {rx.med_cipher_text}
                </td>
                <td className="py-2 pr-4 font-mono text-lazarus-normal font-semibold">
                  {rx.med_decoded_name || '???'}
                </td>
                <td className="py-2 pr-4">
                  {rx.dosage || '--'}
                </td>
                <td className="py-2">
                  {rx.route || '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
