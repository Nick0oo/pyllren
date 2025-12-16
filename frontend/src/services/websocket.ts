import { OpenAPI } from "@/client"

export type WSStatus = "disconnected" | "connecting" | "connected"
export type WSMessage = any

type Listener<T> = (payload: T) => void

const toWebSocketUrl = (base: string): string => {
  if (base.startsWith("ws")) return base
  if (base.startsWith("https://")) return base.replace("https://", "wss://")
  if (base.startsWith("http://")) return base.replace("http://", "ws://")
  return base
}

class WebSocketService {
  private socket: WebSocket | null = null
  private status: WSStatus = "disconnected"
  private statusListeners: Listener<WSStatus>[] = []
  private messageListeners: Listener<WSMessage>[] = []
  private reconnectAttempts = 0
  private manualClose = false
  private readonly maxAttempts = 10
  // No almacenamos baseUrl en el constructor para evitar usar el origen del dev server (5173).
  // Leemos OpenAPI.BASE en tiempo de conexión, cuando ya fue configurado en main.tsx.

  onStatusChange(listener: Listener<WSStatus>): () => void {
    this.statusListeners.push(listener)
    return () => {
      this.statusListeners = this.statusListeners.filter((l) => l !== listener)
    }
  }

  onMessage(listener: Listener<WSMessage>): () => void {
    this.messageListeners.push(listener)
    return () => {
      this.messageListeners = this.messageListeners.filter((l) => l !== listener)
    }
  }

  getStatus(): WSStatus {
    return this.status
  }

  private setStatus(next: WSStatus) {
    this.status = next
    this.statusListeners.forEach((l) => l(next))
  }

  private buildUrl(token: string): string {
    // Determinar base HTTP del backend desde OpenAPI.BASE o, si falta, del window.origin
    const base = (OpenAPI.BASE && OpenAPI.BASE.trim().length > 0)
      ? OpenAPI.BASE
      : (typeof window !== "undefined" ? window.location.origin : "")

    const wsBase = toWebSocketUrl(base)

    // Tomar solo el origen (proto + host + puerto), nunca rutas tipo /api
    let origin = wsBase
    try {
      const u = new URL(wsBase)
      origin = `${u.protocol}//${u.host}`
    } catch {
      // si no es una URL absoluta, caemos a window.origin
      origin = typeof window !== "undefined" ? toWebSocketUrl(window.location.origin) : wsBase
    }

    const trimmed = origin.endsWith("/") ? origin.slice(0, -1) : origin
    // El backend monta todas las rutas bajo /api/v1, incluido el WebSocket
    return `${trimmed}/api/v1/ws?token=${encodeURIComponent(token)}`
  }

  connect(token: string): void {
    if (!token) return
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    this.manualClose = false
    this.setStatus("connecting")
    const url = this.buildUrl(token)
    this.socket = new WebSocket(url)

    this.socket.onopen = () => {
      this.reconnectAttempts = 0
      this.setStatus("connected")
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.messageListeners.forEach((l) => l(data))
      } catch (err) {
        // ignore malformed messages
      }
    }

    this.socket.onclose = (event) => {
      this.setStatus("disconnected")
      this.socket = null
      if (this.manualClose) return
      // Close code 4001/1008/1011 => do not hammer reconnect without token refresh
      if ([4001, 1008, 1011].includes(event.code)) return
      this.scheduleReconnect(token)
    }

    this.socket.onerror = () => {
      // Will trigger onclose
    }
  }

  private scheduleReconnect(token: string) {
    if (this.reconnectAttempts >= this.maxAttempts) return
    this.reconnectAttempts += 1
    const delay = Math.min(1000 * 2 ** (this.reconnectAttempts - 1), 30000)
    setTimeout(() => {
      this.connect(token)
    }, delay)
  }

  disconnect(): void {
    this.manualClose = true
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.setStatus("disconnected")
  }
}

export const websocketService = new WebSocketService()
