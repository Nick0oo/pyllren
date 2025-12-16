import { useEffect, useState } from "react"
import { websocketService, type WSMessage, type WSStatus } from "@/services/websocket"

export const useWebSocket = (token: string | null) => {
  const [status, setStatus] = useState<WSStatus>(websocketService.getStatus())
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null)

  useEffect(() => {
    if (!token) return
    const offStatus = websocketService.onStatusChange(setStatus)
    const offMessage = websocketService.onMessage((msg) => setLastMessage(msg))
    websocketService.connect(token)
    return () => {
      offStatus()
      offMessage()
    }
  }, [token])

  useEffect(() => {
    if (!token) {
      websocketService.disconnect()
    }
  }, [token])

  return {
    status,
    isConnected: status === "connected",
    lastMessage,
  }
}

export default useWebSocket
