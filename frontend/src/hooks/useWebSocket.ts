import { useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import wsClient from '../api/websocket'

export function useWebSocket() {
  const queryClient = useQueryClient()

  useEffect(() => {
    wsClient.connect()

    wsClient.on('vitals_update', () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    })

    wsClient.on('alert_opened', () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
    })

    wsClient.on('alert_closed', () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
    })

    return () => {
      wsClient.disconnect()
    }
  }, [queryClient])

  const subscribeToPatient = useCallback((patientId: string) => {
    wsClient.subscribeToPatient(patientId)
  }, [])

  const unsubscribeFromPatient = useCallback((patientId: string) => {
    wsClient.unsubscribeFromPatient(patientId)
  }, [])

  return { subscribeToPatient, unsubscribeFromPatient }
}
