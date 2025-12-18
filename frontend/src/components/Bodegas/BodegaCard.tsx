import {
  Card,
  Badge,
  HStack,
  VStack,
  Text,
  Box,
  Flex,
} from "@chakra-ui/react"
import { FiMapPin, FiThermometer, FiDroplet } from "react-icons/fi"
import { useQuery } from "@tanstack/react-query"
import type { BodegaPublicExtended, BodegaPublic } from "@/hooks/useBodegas"
import { useBodegas } from "@/hooks/useBodegas"
import EditBodega from "./EditBodega"
import DeleteBodega from "./DeleteBodega"

type Props = {
  bodega: BodegaPublicExtended | BodegaPublic
}

const BodegaCard = ({ bodega }: Props) => {
  // Verificar si es extendido o básico
  const isExtended = "total_lotes" in bodega
  
  // Si no es extendido, cargar datos extendidos
  const { getBodegaQuery } = useBodegas()
  const { data: extendedData } = useQuery(
    getBodegaQuery(bodega.id_bodega)
  )
  
  // Usar datos extendidos si están disponibles, sino usar datos básicos
  const extendedBodega = (extendedData || (isExtended ? bodega : null)) as BodegaPublicExtended | null
  const displayBodega = extendedBodega || bodega
  
  // Calcular porcentaje de ocupación básico
  // Por ahora usamos total_productos como aproximación de ocupación
  // En el futuro el backend calculará ocupacion_actual
  const ocupacionActual = extendedBodega ? (extendedBodega.total_productos || 0) : 0
  const ocupacionPorcentaje =
    bodega.capacidad > 0
      ? Math.min((ocupacionActual / bodega.capacidad) * 100, 100)
      : 0
  
  const totalLotes = extendedBodega ? extendedBodega.total_lotes : 0
  const totalProductos = extendedBodega ? extendedBodega.total_productos : 0

  const temperaturaStr =
    bodega.temperatura_min !== null && bodega.temperatura_max !== null
      ? `${bodega.temperatura_min}-${bodega.temperatura_max}°C`
      : "N/A"

  const humedadStr =
    bodega.humedad_min !== null && bodega.humedad_max !== null
      ? `${bodega.humedad_min}-${bodega.humedad_max}%`
      : "N/A"

  return (
    <Card.Root>
      <Card.Header>
        <Flex justify="space-between" align="center">
          <VStack align="start" gap={1}>
            <Text fontWeight="bold" fontSize="lg">
              {bodega.nombre}
            </Text>
            <Text fontSize="sm" color="gray.600">
              {bodega.tipo}
            </Text>
          </VStack>
          {bodega.estado && (
            <Badge colorPalette="green" size="lg">
              Operativa
            </Badge>
          )}
        </Flex>
      </Card.Header>
      <Card.Body>
        <VStack align="stretch" gap={3}>
          {/* Ubicación */}
          {bodega.ubicacion && (
            <HStack>
              <FiMapPin color="gray" />
              <Text fontSize="sm" color="gray.600">
                {bodega.ubicacion}
              </Text>
            </HStack>
          )}

          {/* Barra de Ocupación */}
          <VStack align="stretch" gap={1}>
            <HStack justify="space-between">
              <Text fontSize="sm" fontWeight="medium">
                Ocupación
              </Text>
              <Text fontSize="sm" color="gray.600">
                {ocupacionActual} / {bodega.capacidad} ({ocupacionPorcentaje.toFixed(0)}%)
              </Text>
            </HStack>
            <Box
              width="100%"
              height="8px"
              borderRadius="full"
              backgroundColor="gray.100"
              position="relative"
              overflow="hidden"
            >
              <Box
                height="100%"
                width={`${ocupacionPorcentaje}%`}
                backgroundColor="green.500"
                borderRadius="full"
                transition="width 0.3s ease"
              />
            </Box>
          </VStack>

          {/* Condiciones Ambientales */}
          <HStack gap={4}>
            <HStack>
              <FiThermometer color="gray" />
              <Text fontSize="sm" color="gray.600">
                {temperaturaStr}
              </Text>
            </HStack>
            <HStack>
              <FiDroplet color="gray" />
              <Text fontSize="sm" color="gray.600">
                {humedadStr}
              </Text>
            </HStack>
          </HStack>

          {/* Inventario */}
          <HStack gap={4}>
            <Text fontSize="sm" color="gray.600">
              <strong>Lotes:</strong> {totalLotes}
            </Text>
            <Text fontSize="sm" color="gray.600">
              <strong>Productos:</strong> {totalProductos}
            </Text>
          </HStack>
        </VStack>
      </Card.Body>
      <Card.Footer>
        <HStack gap={2}>
          <EditBodega bodega={displayBodega as any} />
          <DeleteBodega bodega={displayBodega as any} />
        </HStack>
      </Card.Footer>
    </Card.Root>
  )
}

export default BodegaCard

