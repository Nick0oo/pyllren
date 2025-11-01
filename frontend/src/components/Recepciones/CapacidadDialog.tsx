import { useState, useEffect } from "react"
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  Table,
  VStack,
  HStack,
  Badge,
  Card,
  Input,
} from "@chakra-ui/react"
import { DialogBody, DialogCloseTrigger, DialogContent, DialogFooter, DialogHeader, DialogRoot } from "@/components/ui/dialog"
import { FiAlertTriangle, FiCheckCircle, FiInfo } from "react-icons/fi"

interface BodegaDistribucion {
  id_bodega: number
  nombre: string
  tipo: string
  cantidad: number
  capacidad_disponible?: number
  ocupacion_actual?: number
  capacidad_total?: number
}

interface CapacidadInsuficienteError {
  error: "capacidad_insuficiente"
  bodega_id: number
  bodega_nombre: string
  capacidad_disponible: number
  capacidad_requerida: number
  excedente: number
  sugerencias_distribucion: {
    bodega_principal: {
      id_bodega: number
      nombre: string
      tipo: string
      capacidad_disponible: number
      cantidad_sugerida: number
      ocupacion_actual: number
      capacidad_total: number
    }
    bodegas_secundarias: Array<{
      id_bodega: number
      nombre_bodega: string
      tipo: string
      cantidad: number
      porcentaje_ocupacion_resultante: number
    }>
    mensaje: string
  }
}

interface CapacidadDialogProps {
  error: CapacidadInsuficienteError
  onConfirm: (distribucion: BodegaDistribucion[]) => void
  onCancel: () => void
  productosOriginales: Array<{
    nombre_comercial: string
    cantidad: number
  }>
}

export function CapacidadDialog({
  error,
  onConfirm,
  onCancel,
  productosOriginales,
}: CapacidadDialogProps) {
  // Estado para la distribución editable
  const [distribucion, setDistribucion] = useState<BodegaDistribucion[]>([])
  const [totalAsignado, setTotalAsignado] = useState(0)

  // Inicializar distribución con las sugerencias del backend
  useEffect(() => {
    const distribucionInicial: BodegaDistribucion[] = [
      {
        id_bodega: error.sugerencias_distribucion.bodega_principal.id_bodega,
        nombre: error.sugerencias_distribucion.bodega_principal.nombre,
        tipo: error.sugerencias_distribucion.bodega_principal.tipo,
        cantidad: error.sugerencias_distribucion.bodega_principal.cantidad_sugerida,
        capacidad_disponible: error.sugerencias_distribucion.bodega_principal.capacidad_disponible,
        ocupacion_actual: error.sugerencias_distribucion.bodega_principal.ocupacion_actual,
        capacidad_total: error.sugerencias_distribucion.bodega_principal.capacidad_total,
      },
      ...error.sugerencias_distribucion.bodegas_secundarias.map((b) => ({
        id_bodega: b.id_bodega,
        nombre: b.nombre_bodega,
        tipo: b.tipo,
        cantidad: b.cantidad,
      })),
    ]
    setDistribucion(distribucionInicial)
  }, [error])

  // Recalcular total asignado cuando cambia la distribución
  useEffect(() => {
    const total = distribucion.reduce((sum, b) => sum + b.cantidad, 0)
    setTotalAsignado(total)
  }, [distribucion])

  const handleCantidadChange = (bodegaId: number, nuevaCantidad: number) => {
    setDistribucion((prev) =>
      prev.map((b) =>
        b.id_bodega === bodegaId
          ? { ...b, cantidad: Math.max(0, nuevaCantidad) }
          : b
      )
    )
  }

  const handleRemoveBodega = (bodegaId: number) => {
    setDistribucion((prev) => prev.filter((b) => b.id_bodega !== bodegaId))
  }

  const isDistribucionValida = totalAsignado === error.capacidad_requerida

  return (
    <DialogRoot open={true} size="xl">
      <DialogContent>
        <DialogHeader>
          <Heading size="lg">
            <Flex align="center" gap={2}>
              <FiAlertTriangle color="orange" />
              Capacidad Insuficiente
            </Flex>
          </Heading>
        </DialogHeader>

        <DialogBody>
          <VStack gap={4} align="stretch">
            {/* Alerta Principal */}
            <Box bg="orange.50" p={4} borderRadius="md" borderWidth={1} borderColor="orange.200">
              <Flex align="start" gap={3}>
                <Box color="orange.500" mt={1}>
                  <FiAlertTriangle size={20} />
                </Box>
                <Box flex={1}>
                  <Text fontWeight="bold" color="orange.700" mb={1}>
                    Bodega sin capacidad suficiente
                  </Text>
                  <Text fontSize="sm" color="orange.900">
                    La bodega <strong>"{error.bodega_nombre}"</strong> tiene solo{" "}
                    <strong>{error.capacidad_disponible}</strong> unidades disponibles
                    pero necesitas almacenar{" "}
                    <strong>{error.capacidad_requerida}</strong> unidades.
                    <br />
                    <Text fontWeight="bold" color="orange.600" mt={1}>
                      Excedente: {error.excedente} unidades
                    </Text>
                  </Text>
                </Box>
              </Flex>
            </Box>

            {/* Mensaje del Backend */}
            <Box bg="blue.50" p={3} borderRadius="md" borderWidth={1} borderColor="blue.200">
              <Flex align="center" gap={2}>
                <FiInfo color="blue" />
                <Text fontSize="sm" color="blue.700">
                  {error.sugerencias_distribucion.mensaje}
                </Text>
              </Flex>
            </Box>

            {/* Tabla de Distribución */}
            <Box>
              <Heading size="md" mb={3}>
                Distribución Sugerida
              </Heading>

              <Table.Root size="sm" variant="outline">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Bodega</Table.ColumnHeader>
                    <Table.ColumnHeader>Tipo</Table.ColumnHeader>
                    <Table.ColumnHeader>Capacidad</Table.ColumnHeader>
                    <Table.ColumnHeader>Cantidad a Asignar</Table.ColumnHeader>
                    <Table.ColumnHeader>Acciones</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {distribucion.map((bodega, index) => (
                    <Table.Row key={bodega.id_bodega}>
                      <Table.Cell>
                        <Flex align="center" gap={2}>
                          <Text fontWeight="medium">{bodega.nombre}</Text>
                          {index === 0 && (
                            <Badge colorScheme="blue" size="sm">
                              Principal
                            </Badge>
                          )}
                        </Flex>
                      </Table.Cell>
                      <Table.Cell>
                        <Badge variant="subtle" colorScheme="gray">
                          {bodega.tipo}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell>
                        {bodega.capacidad_disponible ? (
                          <Text fontSize="sm" color="gray.600">
                            {bodega.capacidad_disponible} / {bodega.capacidad_total}
                          </Text>
                        ) : (
                          <Text fontSize="sm" color="gray.400">
                            N/A
                          </Text>
                        )}
                      </Table.Cell>
                      <Table.Cell>
                        <Input
                          type="number"
                          value={bodega.cantidad}
                          min={0}
                          max={bodega.capacidad_disponible || 999999}
                          onChange={(e) =>
                            handleCantidadChange(bodega.id_bodega, Number(e.target.value))
                          }
                          size="sm"
                          width="100px"
                        />
                      </Table.Cell>
                      <Table.Cell>
                        {index > 0 && (
                          <Button
                            size="xs"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => handleRemoveBodega(bodega.id_bodega)}
                          >
                            Remover
                          </Button>
                        )}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>

            {/* Resumen de Asignación */}
            <Card.Root>
              <Card.Body>
                <Flex justify="space-between" align="center">
                  <Box>
                    <Text fontSize="sm" color="gray.600">
                      Total Asignado
                    </Text>
                    <Text fontSize="2xl" fontWeight="bold">
                      {totalAsignado} unidades
                    </Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.600">
                      Total Requerido
                    </Text>
                    <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                      {error.capacidad_requerida} unidades
                    </Text>
                  </Box>
                  <Box>
                    {isDistribucionValida ? (
                      <Flex align="center" gap={2} color="green.600">
                        <FiCheckCircle size={24} />
                        <Text fontWeight="bold">✓ Válido</Text>
                      </Flex>
                    ) : (
                      <Flex align="center" gap={2} color="red.600">
                        <FiAlertTriangle size={24} />
                        <Text fontWeight="bold">
                          Falta: {error.capacidad_requerida - totalAsignado}
                        </Text>
                      </Flex>
                    )}
                  </Box>
                </Flex>
              </Card.Body>
            </Card.Root>

            {/* Lista de Productos */}
            <Box>
              <Heading size="sm" mb={2} color="gray.600">
                Productos en este lote
              </Heading>
              <Box maxH="150px" overflowY="auto" bg="gray.50" p={2} borderRadius="md">
                {productosOriginales.map((prod, idx) => (
                  <Text key={idx} fontSize="sm">
                    • {prod.nombre_comercial} - {prod.cantidad} unidades
                  </Text>
                ))}
              </Box>
            </Box>
          </VStack>
        </DialogBody>

        <DialogFooter>
          <HStack>
            <Button variant="outline" onClick={onCancel}>
              Cancelar
            </Button>
            <Button
              colorScheme="blue"
              onClick={() => onConfirm(distribucion)}
              disabled={!isDistribucionValida}
            >
              Confirmar Distribución
            </Button>
          </HStack>
        </DialogFooter>

        <DialogCloseTrigger onClick={onCancel} />
      </DialogContent>
    </DialogRoot>
  )
}
