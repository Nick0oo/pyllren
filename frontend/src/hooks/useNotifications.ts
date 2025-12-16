import { useCallback, useEffect, useMemo, useState } from "react"
import { OpenAPI } from "@/client"
import { request as apiRequest } from "@/client/core/request"
import useWebSocket from "@/hooks/useWebSocket"
import { handleError } from "@/utils"

export type NotificationItem = {
  id: number
  tipo: string
  payload: any
  creado_en: string
  prioridad?: string
  leida: boolean
}

type ListResponse = {
  data: NotificationItem[]
  count: number
}

const fetchNotifications = async (): Promise<ListResponse> => {
  return apiRequest(OpenAPI, {
    method: "GET",
    url: "/api/v1/notifications/",
    query: {
      skip: 0,
      limit: 50,
    },
  })
}

const markReadRequest = async (id: number): Promise<NotificationItem> => {
  return apiRequest(OpenAPI, {
    method: "PATCH",
    url: `/api/v1/notifications/${id}/read`,
  })
}

const deleteNotificationRequest = async (id: number): Promise<{ deleted: boolean }> => {
  return apiRequest(OpenAPI, {
    method: "DELETE",
    url: `/api/v1/notifications/${id}`,
  })
}

export const useNotifications = () => {
  const token = useMemo(() => localStorage.getItem("access_token"), [])
  const { isConnected, lastMessage } = useWebSocket(token)
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [initialSynced, setInitialSynced] = useState<boolean>(false)

  const syncInitial = useCallback(async () => {
    try {
      const res = await fetchNotifications()
      setNotifications(res.data)
      const unread = res.data.filter((n) => !n.leida).length
      setUnreadCount(unread)
      setInitialSynced(true)
    } catch (err: any) {
      handleError(err)
    }
  }, [])

  useEffect(() => {
    if (isConnected && !initialSynced) {
      void syncInitial()
    }
  }, [isConnected, initialSynced, syncInitial])

  useEffect(() => {
    if (!lastMessage) return
    if (typeof lastMessage !== "object") return
    if (!lastMessage.notification_id) return

    // Si llega una confirmación/cancelación, eliminar cualquier notificación previa relacionada
    const tId = lastMessage?.payload?.transferencia_id
    if (tId && (lastMessage.type === "transferencia:confirmada" || lastMessage.type === "transferencia:cancelada")) {
      setNotifications((prev) => prev.filter((n) => n?.payload?.transferencia_id !== tId || (n.tipo !== "transferencia:admin" && n.tipo !== "transferencia:pendiente")))
    }

    const newNotif: NotificationItem = {
      id: lastMessage.notification_id,
      tipo: lastMessage.type,
      payload: lastMessage.payload,
      creado_en: lastMessage.created_at,
      prioridad: lastMessage.priority,
      leida: false,
    }
    setNotifications((prev) => [newNotif, ...prev])
    setUnreadCount((prev) => prev + 1)
  }, [lastMessage])

  const markAsRead = useCallback(async (id: number) => {
    try {
      await markReadRequest(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, leida: true } : n)),
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (err: any) {
      handleError(err)
    }
  }, [])

  const removeNotification = useCallback((id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const deleteNotification = useCallback(async (id: number) => {
    try {
      // Marcar como leída en backend si aún no lo está
      const target = notifications.find((n) => n.id === id)
      if (target && !target.leida) {
        try {
          await markReadRequest(id)
        } catch {}
      }

      await deleteNotificationRequest(id)

      // Actualizar estado y contador de no leídas de forma consistente
      setNotifications((prev) => {
        const victim = prev.find((n) => n.id === id)
        if (victim && !victim.leida) {
          setUnreadCount((c) => Math.max(0, c - 1))
        }
        return prev.filter((n) => n.id !== id)
      })
    } catch (err: any) {
      handleError(err)
    }
  }, [notifications])

  const markAllAsRead = useCallback(async () => {
    try {
      const unread = notifications.filter((n) => !n.leida)
      // Fire-and-forget sequentially to keep it simple in local dev
      for (const n of unread) {
        try {
          await markReadRequest(n.id)
        } catch {}
      }
      setNotifications((prev) => prev.map((n) => ({ ...n, leida: true })))
      setUnreadCount(0)
    } catch (err: any) {
      handleError(err)
    }
  }, [notifications])

  return {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    removeNotification,
    deleteNotification,
  }
}

export default useNotifications
