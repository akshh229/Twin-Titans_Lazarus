import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import type { Alert, AlertHistory } from '../types'

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const { data } = await api.get<Alert[]>('/alerts')
      return data
    },
    refetchInterval: 5000,
  })
}

export function useAlertHistory(patientId: string) {
  return useQuery({
    queryKey: ['alertHistory', patientId],
    queryFn: async () => {
      const { data } = await api.get<AlertHistory[]>(`/alerts/history/${patientId}`)
      return data
    },
    enabled: !!patientId,
  })
}
