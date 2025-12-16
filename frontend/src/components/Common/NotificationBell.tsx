import { FaBell } from "react-icons/fa"
import {
  Popover,
  Button,
  Badge,
  Flex,
  Text,
  VStack,
  Portal,
} from "@chakra-ui/react"
import { useNotifications } from "../../hooks/useNotifications"
import NotificationItem from "../Common/NotificationItem"
import useAuth from "@/hooks/useAuth"
import { useWebSocket } from "@/hooks/useWebSocket"

export const NotificationBell = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification, deleteNotification } = useNotifications()
  const { user } = useAuth()
  const canActOnTransfers = !!(user?.is_superuser || user?.id_rol === 1)
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null
  const { status, isConnected } = useWebSocket(token)

  return (
    <Popover.Root
      positioning={{ placement: "bottom-start", gutter: 8, flip: true }}
      closeOnInteractOutside
      lazyMount
      modal
    >
      <Popover.Trigger asChild>
        <Button
          variant="ghost"
          position="relative"
          p={2}
          aria-label="Notificaciones"
        >
          <FaBell />

          {unreadCount > 0 && (
            <Badge
              position="absolute"
              top="0"
              right="0"
              transform="translate(25%, -25%)"
              colorScheme="red"
              borderRadius="full"
              fontSize="0.7rem"
              px={2}
            >
              {unreadCount}
            </Badge>
          )}
        </Button>
      </Popover.Trigger>

      <Portal>
        <Popover.Positioner>
          <Popover.Content
            position="relative"
            maxW="380px"
            width="380px"
            bg="bg.surface"
            borderRadius="md"
            boxShadow="xl"
            borderWidth="1px"
            zIndex={2000}
          >
          <Popover.Arrow>
            <Popover.ArrowTip />
          </Popover.Arrow>

          <Popover.Header fontWeight="bold" px={4} py={3} borderBottomWidth="1px" bg="bg.subtle">
            <Flex justify="space-between" align="center">
              <Text>Notificaciones</Text>
              <Flex align="center" gap={2}>
                <Badge colorScheme={isConnected ? "green" : status === "connecting" ? "yellow" : "red"}>
                  {status === "connected" ? "WS: Conectado" : status === "connecting" ? "WS: Conectando" : "WS: Desconectado"}
                </Badge>
                <Text fontSize="xs" color="fg.muted">
                  Últimas 10
                </Text>
                <Button size="xs" variant="outline" onClick={() => markAllAsRead()}>
                  Marcar todas
                </Button>
              </Flex>
            </Flex>
          </Popover.Header>

          <Popover.Body px={4} py={3}>
            <VStack gap={3} maxH="420px" overflowY="auto">
              {notifications.length === 0 && (
                <Text fontSize="sm" color="fg.muted">
                  Sin notificaciones
                </Text>
              )}

              {notifications.slice(0, 10).map((n) => (
                <NotificationItem
                  key={n.id}
                  notification={n}
                  onMarkRead={markAsRead}
                  onRemove={removeNotification}
                  onDelete={deleteNotification}
                  canActOnTransfers={canActOnTransfers}
                />
              ))}
            </VStack>

            <Flex mt={3}>
              <Button asChild variant="ghost" size="sm" w="full">
                <a href="/notifications">Ver todas</a>
              </Button>
            </Flex>
          </Popover.Body>
          </Popover.Content>
        </Popover.Positioner>
      </Portal>
    </Popover.Root>
  )
}
export default NotificationBell
