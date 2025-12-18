import { Box, Heading, HStack, Skeleton, Stack, Table, Text, VStack } from "@chakra-ui/react"
import { useRecepciones } from "@/hooks/useRecepciones"
import { useAlcance } from "@/hooks/useAlcance"

const LotesList = () => {
  const alcance = useAlcance()
  const { lotesQuery } = useRecepciones({
    id_sucursal: alcance.scopeSucursalId ?? null,
  })

  if (lotesQuery.isLoading) {
    return (
      <Stack gap={2}>
        <Skeleton height="40px" />
        <Skeleton height="200px" />
      </Stack>
    )
  }

  const lotes = (lotesQuery.data as any)?.data || []
  const count = (lotesQuery.data as any)?.count || 0

  return (
    <Box p={4} borderWidth="1px" borderRadius="md" bg="bg.surface">
      <VStack align="stretch" gap={4}>
        <HStack justify="space-between">
          <Heading size="md">Lotes Creados</Heading>
          <Text color="fg.muted" fontSize="sm">
            {count} {count === 1 ? "lote" : "lotes"}
          </Text>
        </HStack>

        {lotes.length === 0 ? (
          <Text color="fg.muted" textAlign="center" py={8}>
            No hay lotes registrados
          </Text>
        ) : (
          <Table.Root size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>Número de Lote</Table.ColumnHeader>
                <Table.ColumnHeader>Fecha Registro</Table.ColumnHeader>
                <Table.ColumnHeader>Estado</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {lotes.slice(0, 10).map((lote: any) => (
                <Table.Row key={lote.id_lote}>
                  <Table.Cell>
                    <Text fontWeight="medium" fontSize="sm">
                      {lote.numero_lote}
                    </Text>
                  </Table.Cell>
                  <Table.Cell>
                    <Text fontSize="sm" color="fg.muted">
                      {lote.fecha_registro
                        ? new Date(lote.fecha_registro).toLocaleString("es-ES", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "-"}
                    </Text>
                  </Table.Cell>
                  <Table.Cell>
                    <Text
                      fontSize="sm"
                      color={
                        lote.estado === "Activo"
                          ? "green.500"
                          : lote.estado === "Vencido"
                          ? "red.500"
                          : "gray.500"
                      }
                    >
                      {lote.estado || "Activo"}
                    </Text>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        )}
      </VStack>
    </Box>
  )
}

export default LotesList

