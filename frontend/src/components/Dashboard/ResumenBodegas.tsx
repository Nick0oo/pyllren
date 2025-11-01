import {
  Card,
  Flex,
  Heading,
  Text,
  Button,
  VStack,
  HStack,
  Box,
  EmptyState,
} from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { FiBox, FiArrowRight } from "react-icons/fi"

import { useBodegas } from "@/hooks/useBodegas"

interface ResumenBodegasProps {
  id_sucursal?: number | null
}

const ResumenBodegas = ({ id_sucursal }: ResumenBodegasProps) => {
  const navigate = useNavigate()
  const { bodegasQuery } = useBodegas({
    id_sucursal: id_sucursal || null,
  })

  const bodegas = bodegasQuery.data?.data || []
  const top3Bodegas = bodegas.slice(0, 3)

  const handleGestionar = () => {
    navigate({ to: "/bodegas", search: { q: "", tipo: "" } })
  }

  if (bodegasQuery.isLoading) {
    return (
      <Card.Root>
        <Card.Header>
          <Flex justify="space-between" align="center">
            <Heading size="md">Resumen por Bodega</Heading>
            <Button size="sm" variant="ghost" disabled>
              gestionar
            </Button>
          </Flex>
          <Text fontSize="sm" color="gray.600">
            Estado actual de las bodegas
          </Text>
        </Card.Header>
        <Card.Body>
          <Text color="gray.500">Cargando bodegas...</Text>
        </Card.Body>
      </Card.Root>
    )
  }

  if (!bodegas || bodegas.length === 0) {
    return (
      <Card.Root>
        <Card.Header>
          <Flex justify="space-between" align="center">
            <Heading size="md">Resumen por Bodega</Heading>
            <Button size="sm" variant="ghost" onClick={handleGestionar}>
              gestionar
              <FiArrowRight />
            </Button>
          </Flex>
          <Text fontSize="sm" color="gray.600">
            Estado actual de las bodegas
          </Text>
        </Card.Header>
        <Card.Body>
          <EmptyState.Root>
            <EmptyState.Content>
              <EmptyState.Indicator>
                <FiBox />
              </EmptyState.Indicator>
              <VStack>
                <EmptyState.Title>No hay bodegas disponibles</EmptyState.Title>
                <EmptyState.Description>
                  No se encontraron bodegas para esta sucursal
                </EmptyState.Description>
              </VStack>
            </EmptyState.Content>
          </EmptyState.Root>
        </Card.Body>
      </Card.Root>
    )
  }

  return (
    <Card.Root>
      <Card.Header>
        <Flex justify="space-between" align="center">
          <Heading size="md">Resumen por Bodega</Heading>
          <Button size="sm" variant="ghost" onClick={handleGestionar}>
            gestionar
            <FiArrowRight />
          </Button>
        </Flex>
        <Text fontSize="sm" color="gray.600">
          Estado actual de las bodegas
        </Text>
      </Card.Header>
      <Card.Body>
        <VStack gap={4} align="stretch">
          {top3Bodegas.map((bodega) => {
            const capacidad = bodega.capacidad || 1000
            
            // Por ahora mostramos porcentaje placeholder
            // En el futuro se puede calcular con datos reales de ocupación
            const ocupacionPorcentaje = 0
            
            // Determinar color según ocupación
            let colorScheme = "blue"
            if (ocupacionPorcentaje >= 90) {
              colorScheme = "red"
            } else if (ocupacionPorcentaje >= 70) {
              colorScheme = "yellow"
            } else if (ocupacionPorcentaje >= 50) {
              colorScheme = "green"
            }

            return (
              <Box
                key={bodega.id_bodega}
                p={4}
                borderWidth="1px"
                borderRadius="md"
                borderColor="gray.200"
                _hover={{ borderColor: "gray.300", bg: "gray.50" }}
              >
                <Flex justify="space-between" align="start" mb={3}>
                  <VStack align="start" gap={1}>
                    <HStack>
                      <FiBox color={`${colorScheme}.500`} />
                      <Text fontWeight="bold" fontSize="md">
                        {bodega.nombre}
                      </Text>
                    </HStack>
                    <Text fontSize="xs" color="gray.600">
                      {bodega.tipo} • {bodega.estado ? "Operativa" : "Inactiva"}
                    </Text>
                  </VStack>
                  <Text fontSize="sm" color="gray.600">
                    Capacidad: {capacidad}
                  </Text>
                </Flex>

                <Flex justify="space-between" fontSize="xs" color="gray.600">
                  <Text>{bodega.descripcion || "Sin descripción"}</Text>
                </Flex>
              </Box>
            )
          })}
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}

export default ResumenBodegas
