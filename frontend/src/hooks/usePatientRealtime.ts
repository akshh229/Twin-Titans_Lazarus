import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { createWebSocketUrl } from '../api/websocket'
import type {
  AlertClosedMessage,
  AlertOpenedMessage,
  Patient,
  VitalsResponse,
  VitalsUpdateMessage,
} from '../types'

type ConnectionState = 'connecting' | 'live' | 'offline'

type RealtimeMessage =
  | AlertClosedMessage
  | AlertOpenedMessage
  | VitalsUpdateMessage
  | { type: 'pong'; timestamp: string }

function mergeVitalsIntoPatient(
  patient: Patient | undefined,
  message: VitalsUpdateMessage
) {
  if (!patient) {
    return patient
  }

  return {
    ...patient,
    last_bpm: message.bpm,
    last_oxygen: message.oxygen,
    last_vitals_timestamp: message.timestamp,
  }
}

function mergeAlertStateIntoPatient(
  patient: Patient | undefined,
  hasActiveAlert: boolean,
  lastBpm?: number | null
) {
  if (!patient) {
    return patient
  }

  return {
    ...patient,
    has_active_alert: hasActiveAlert,
    last_bpm: lastBpm ?? patient.last_bpm,
  }
}

function mergeVitalsIntoHistory(
  response: VitalsResponse | undefined,
  message: VitalsUpdateMessage
) {
  if (!response) {
    return response
  }

  const nextPoint = {
    timestamp: message.timestamp,
    bpm: message.bpm,
    oxygen: message.oxygen,
    quality_flag: 'good',
  }

  const windowStart = Date.parse(response.start_time)
  const nextTimestamp = Date.parse(message.timestamp)
  const deduped = response.data.filter((point) => point.timestamp !== message.timestamp)

  if (!Number.isNaN(nextTimestamp) && nextTimestamp >= windowStart) {
    deduped.push(nextPoint)
  }

  deduped.sort((left, right) => Date.parse(left.timestamp) - Date.parse(right.timestamp))

  return {
    ...response,
    end_time: message.timestamp,
    data: deduped,
  }
}

export function usePatientRealtime(patientId: string) {
  const queryClient = useQueryClient()
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    patientId ? 'connecting' : 'offline'
  )
  const [lastMessageAt, setLastMessageAt] = useState<string | null>(null)

  useEffect(() => {
    if (!patientId) {
      setConnectionState('offline')
      setLastMessageAt(null)
      return
    }

    setConnectionState('connecting')
    const socket = new WebSocket(createWebSocketUrl(`/ws/vitals/${patientId}`))

    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }))
      }
    }, 15000)

    socket.onopen = () => {
      setConnectionState('live')
    }

    socket.onerror = () => {
      setConnectionState('offline')
    }

    socket.onclose = () => {
      setConnectionState('offline')
    }

    socket.onmessage = (event) => {
      let message: RealtimeMessage

      try {
        message = JSON.parse(event.data) as RealtimeMessage
      } catch {
        return
      }

      if (message.type === 'pong') {
        return
      }

      setConnectionState('live')
      setLastMessageAt(new Date().toISOString())

      if (message.type === 'vitals_update') {
        queryClient.setQueryData(['patient', patientId], (current: Patient | undefined) =>
          mergeVitalsIntoPatient(current, message)
        )
        queryClient.setQueryData(['patients'], (current: Patient[] | undefined) =>
          current?.map((patient) =>
            patient.patient_id === message.patient_id
              ? mergeVitalsIntoPatient(patient, message)!
              : patient
          )
        )
        queryClient.setQueriesData(
          { queryKey: ['vitals', patientId] },
          (current: VitalsResponse | undefined) => mergeVitalsIntoHistory(current, message)
        )
        return
      }

      if (message.type === 'alert_opened') {
        queryClient.setQueryData(['patient', patientId], (current: Patient | undefined) =>
          mergeAlertStateIntoPatient(current, true, message.last_bpm)
        )
        queryClient.setQueryData(['patients'], (current: Patient[] | undefined) =>
          current?.map((patient) =>
            patient.patient_id === message.patient_id
              ? mergeAlertStateIntoPatient(patient, true, message.last_bpm)!
              : patient
          )
        )
        queryClient.invalidateQueries({ queryKey: ['alerts'] })
        queryClient.invalidateQueries({ queryKey: ['alertHistory', patientId] })
        return
      }

      queryClient.setQueryData(['patient', patientId], (current: Patient | undefined) =>
        mergeAlertStateIntoPatient(current, false)
      )
      queryClient.setQueryData(['patients'], (current: Patient[] | undefined) =>
        current?.map((patient) =>
          patient.patient_id === message.patient_id
            ? mergeAlertStateIntoPatient(patient, false)!
            : patient
        )
      )
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alertHistory', patientId] })
    }

    return () => {
      window.clearInterval(heartbeat)
      socket.close()
    }
  }, [patientId, queryClient])

  return { connectionState, lastMessageAt }
}
