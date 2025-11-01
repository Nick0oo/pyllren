import { Box, Container, Flex, Heading, Text, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useState, useEffect } from "react"

import useAuth from "@/hooks/useAuth"
import { useAlcance } from "@/hooks/useAlcance"
import { usePermissions } from "@/hooks/usePermissions"
import StatsCards from "@/components/Dashboard/StatsCards"
import ResumenBodegas from "@/components/Dashboard/ResumenBodegas"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const alcance = useAlcance()
  const { isAdmin } = usePermissions()
  const [filterSucursal, setFilterSucursal] = useState<number | null>(
    alcance.scopeSucursalId
  )

  // Determinar id_sucursal para el dashboard: admin puede filtrar, no-admin usa su sucursal automáticamente
  const idSucursalQuery = isAdmin() ? filterSucursal : alcance.scopeSucursalId

  // Actualizar filtro de sucursal cuando cambie el alcance (para no-admin)
  useEffect(() => {
    if (!isAdmin() && alcance.scopeSucursalId !== null) {
      setFilterSucursal(alcance.scopeSucursalId)
    }
  }, [alcance.scopeSucursalId, isAdmin])

  return (
    <Container maxW="full">
      <VStack align="stretch" gap={6} pt={12} m={4}>
        {/* Saludo personalizado */}
        <Box>
          <Heading size="xl" mb={2}>
            Hola, {currentUser?.full_name || currentUser?.email} 👋🏼
          </Heading>
          <Text color="gray.600">¡Qué gusto tenerte de vuelta!</Text>
        </Box>

        {/* Filtro de sucursal - Solo admin puede cambiar */}
        {isAdmin() && alcance.sucursales.length > 0 && (
          <Flex align="center" gap={3}>
            <Text fontSize="sm" fontWeight="medium" color="gray.700">
              Ver datos de:
            </Text>
            <select
              style={{
                width: "250px",
                height: "36px",
                padding: "6px 12px",
                fontSize: "14px",
                border: "1px solid #e2e8f0",
                borderRadius: "6px",
              }}
              value={filterSucursal || ""}
              onChange={(e) => {
                const id = e.target.value ? Number(e.target.value) : null
                setFilterSucursal(id)
              }}
            >
              <option value="">Todas las sucursales</option>
              {alcance.sucursales.map((sucursal) => (
                <option key={sucursal.id_sucursal} value={sucursal.id_sucursal}>
                  {sucursal.nombre}
                </option>
              ))}
            </select>
          </Flex>
        )}

        {/* Stats Cards - 3 tarjetas principales */}
        <StatsCards id_sucursal={idSucursalQuery} />

        {/* Resumen de Bodegas */}
        <ResumenBodegas id_sucursal={idSucursalQuery} />
      </VStack>
    </Container>
  )
}
