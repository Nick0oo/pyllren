import { Box, Button, Flex, IconButton, Text } from "@chakra-ui/react"
import type { NotificationItem } from "@/hooks/useNotifications"
import { OpenAPI } from "@/client"
import { request as apiRequest } from "@/client/core/request"
import { handleError } from "@/utils"
import { FaTrash } from "react-icons/fa"

interface Props {
  notification: NotificationItem
  onMarkRead: (id: number) => Promise<void>
  onActionCompleted?: (id: number) => void
  onRemove?: (id: number) => void
  onDelete?: (id: number) => Promise<void>
  canActOnTransfers?: boolean
}

const actionTransferencia = async (
  notification: NotificationItem,
  action: "confirmar" | "cancelar",
) => {
  const id = notification.payload?.transferencia_id
  if (!id) throw new Error("transferencia_id faltante")
  await apiRequest(OpenAPI, {
    method: "PATCH",
    url: `/api/v1/transferencias/${id}/${action}`,
  })
}

const NotificationItem = ({ notification, onMarkRead, onActionCompleted, onRemove, onDelete, canActOnTransfers = false }: Props) => {
  const { tipo, payload, creado_en, leida } = notification

  const handleAction = async (action: "confirmar" | "cancelar") => {
    try {
      await actionTransferencia(notification, action)
      await onMarkRead(notification.id)
      if (onRemove) onRemove(notification.id)
      if (onActionCompleted) onActionCompleted(notification.id)
    } catch (err: any) {
      handleError(err)
    }
  }

  const renderBody = () => {
    if (tipo === "transferencia:pendiente") {
      return (
        <>
          <Text fontWeight="medium">Nueva transferencia recibida</Text>
          <Text fontSize="sm" color="gray.600">
            Origen: {payload?.origen} → Destino: {payload?.destino}
          </Text>
          {canActOnTransfers && (
            <Flex gap={2} mt={2} wrap="wrap">
              <Button size="xs" onClick={() => handleAction("confirmar")}>Confirmar</Button>
              <Button size="xs" variant="outline" onClick={() => handleAction("cancelar")}>
                Cancelar
              </Button>
            </Flex>
          )}
        </>
      )
    }
    if (tipo === "transferencia:info_destino") {
      return (
        <>
          <Text fontWeight="medium">Aviso de transferencia</Text>
          <Text fontSize="sm" color="gray.600">
            {payload?.usuario_origen_nombre ? (
              `${payload?.usuario_origen_nombre} ha transferido ${payload?.lotes?.[0]?.numero_lote ? `el lote ${payload?.lotes?.[0]?.numero_lote}` : "un lote"} de la bodega ${payload?.origen} a la bodega ${payload?.destino}`
            ) : (
              "Se ha registrado una transferencia"
            )}
          </Text>
        </>
      )
    }
    if (tipo === "transferencia:confirmada") {
      return (
        <>
          <Text fontWeight="medium">Transferencia confirmada</Text>
          <Text fontSize="sm" color="gray.600">Destino: {payload?.destino}</Text>
        </>
      )
    }
    if (tipo === "transferencia:cancelada") {
      return (
        <>
          <Text fontWeight="medium">Transferencia cancelada</Text>
          <Text fontSize="sm" color="gray.600">Destino: {payload?.destino}</Text>
        </>
      )
    }
    if (tipo === "transferencia:admin") {
      return (
        <>
          <Text fontWeight="medium">Aviso de transferencia</Text>
          <Text fontSize="sm" color="gray.600">
            {payload?.usuario_origen_nombre ? (
              `${payload?.usuario_origen_nombre} ha transferido ${payload?.lotes?.[0]?.numero_lote ? `el lote ${payload?.lotes?.[0]?.numero_lote}` : "un lote"} de la bodega ${payload?.origen} a la bodega ${payload?.destino}`
            ) : (
              payload?.mensaje || "Se ha registrado una transferencia"
            )}
          </Text>
          {canActOnTransfers && (
            <Flex gap={2} mt={2} wrap="wrap">
              <Button size="xs" onClick={() => handleAction("confirmar")}>Confirmar</Button>
              <Button size="xs" variant="outline" onClick={() => handleAction("cancelar")}>Cancelar</Button>
            </Flex>
          )}
        </>
      )
    }
    return (
      <>
        <Text fontWeight="medium">{tipo}</Text>
        <Text fontSize="sm" color="gray.600">{JSON.stringify(payload)}</Text>
      </>
    )
  }

  return (
    <Box
      p={3}
      borderRadius="md"
      bg={leida ? "gray.50" : "blue.50"}
      border="1px solid"
      borderColor={leida ? "gray.100" : "blue.100"}
    >
      <Flex justify="space-between" gap={2} align="flex-start">
        <Box>{renderBody()}</Box>
        <Flex direction="column" align="flex-end" gap={2} minW="80px">
          {!leida && (
            <Button size="xs" variant="ghost" onClick={() => onMarkRead(notification.id)}>
              Marcar leída
            </Button>
          )}
          {onDelete && (
            <IconButton
              aria-label="Borrar notificación"
              title="Borrar notificación"
              size="xs"
              variant="outline"
              colorScheme="red"
              children={<FaTrash />}
              onClick={() => onDelete(notification.id)}
            />
          )}
        </Flex>
      </Flex>
      <Text mt={2} fontSize="xs" color="gray.500">
        {new Date(creado_en).toLocaleString()}
      </Text>
    </Box>
  )
}

export default NotificationItem
