import { io, Socket } from 'socket.io-client'

class WebSocketClient {
  private socket: Socket | null = null
  private listeners: Map<string, Set<(data: any) => void>> = new Map()

  connect() {
    if (this.socket?.connected) return

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    this.socket = io(wsUrl, {
      transports: ['websocket'],
      autoConnect: true,
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    this.socket.on('vitals_update', (data) => {
      this.emit('vitals_update', data)
    })

    this.socket.on('alert_opened', (data) => {
      this.emit('alert_opened', data)
    })

    this.socket.on('alert_closed', (data) => {
      this.emit('alert_closed', data)
    })
  }

  disconnect() {
    this.socket?.disconnect()
    this.socket = null
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)
  }

  off(event: string, callback: (data: any) => void) {
    this.listeners.get(event)?.delete(callback)
  }

  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach((cb) => cb(data))
  }

  subscribeToPatient(patientId: string) {
    this.socket?.emit('subscribe', { type: 'subscribe', patient_id: patientId })
  }

  unsubscribeFromPatient(patientId: string) {
    this.socket?.emit('unsubscribe', { type: 'unsubscribe', patient_id: patientId })
  }
}

export const wsClient = new WebSocketClient()
export default wsClient
