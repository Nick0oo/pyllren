import { Box, Heading, Stack, Text } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import NotificationItem from "@/components/Common/NotificationItem"
import { useNotifications } from "@/hooks/useNotifications"

export const Route = createFileRoute("/_layout/notifications")({
  component: NotificationsPage,
})

function NotificationsPage() {
  const { notifications, markAsRead } = useNotifications()

  return (
    <Box>
      <Heading size="lg" mb={4} pt={8}>
        Notificaciones
      </Heading>
      <Text color="gray.600" mb={6}>
        Historial de notificaciones recientes
      </Text>
      <Stack gap={3}>
        {notifications.length === 0 && (
          <Text color="gray.500">Sin notificaciones</Text>
        )}
        {notifications.map((n) => (
          <NotificationItem key={n.id} notification={n} onMarkRead={markAsRead} />
        ))}
      </Stack>
    </Box>
  )
}

export default NotificationsPage
