import {
  Container,
  Flex,
  Heading,
  Input,
  Text,
} from "@chakra-ui/react"
import { InputGroup } from "@/components/ui/input-group"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { useState, useEffect } from "react"
import { z } from "zod"

import { usePermissions } from "@/hooks/usePermissions"
import { useAlcance } from "@/hooks/useAlcance"
import { useBodegas } from "@/hooks/useBodegas"
import StatsCards from "@/components/Bodegas/StatsCards"
import BodegasList from "@/components/Bodegas/BodegasList"
import AddBodega from "@/components/Bodegas/AddBodega"

const bodegasSearchSchema = z.object({
  q: z.string().catch(""),
  tipo: z.string().catch(""),
  estado: z.boolean().optional(),
})

export const Route = createFileRoute("/_layout/bodegas")({
  component: Bodegas,
  validateSearch: (search) => bodegasSearchSchema.parse(search),
})

function Bodegas() {
  const { canAccessModule, isAdmin } = usePermissions()
  const navigate = useNavigate()
  const { q, tipo } = Route.useSearch()
  const alcance = useAlcance()
  const [searchTerm, setSearchTerm] = useState(q || "")
  const [filterTipo, setFilterTipo] = useState(tipo || "")
  const [filterSucursal, setFilterSucursal] = useState<number | null>(
    alcance.scopeSucursalId
  )

  // Determinar id_sucursal para el query: admin puede filtrar, no-admin usa su sucursal automáticamente
  const idSucursalQuery = isAdmin() ? filterSucursal : alcance.scopeSucursalId

  // Query de bodegas con filtros
  const { bodegasQuery } = useBodegas({
    q: searchTerm || null,
    tipo: filterTipo || null,
    estado: undefined, // Por ahora no filtramos por estado en la UI
    id_sucursal: idSucursalQuery || null,
  })

  // Debounce para la búsqueda
  useEffect(() => {
    const timer = setTimeout(() => {
      // Solo incluir parámetros que tengan valores
      const searchParams: Record<string, string> = {}
      if (searchTerm && searchTerm.trim()) {
        searchParams.q = searchTerm.trim()
      }
      if (filterTipo && filterTipo.trim()) {
        searchParams.tipo = filterTipo.trim()
      }
      
      navigate({
        to: "/bodegas",
        search: searchParams as any,
      })
    }, 500)

    return () => clearTimeout(timer)
  }, [searchTerm, filterTipo, navigate])

  // Actualizar filtro de sucursal cuando cambie el alcance (para no-admin)
  useEffect(() => {
    if (!isAdmin() && alcance.scopeSucursalId !== null) {
      setFilterSucursal(alcance.scopeSucursalId)
    }
  }, [alcance.scopeSucursalId, isAdmin])

  // Verificar permisos de acceso - permitir tanto admin como inventory
  if (!canAccessModule("admin") && !canAccessModule("inventory")) {
    navigate({ to: "/" })
    return null
  }

  const bodegas = bodegasQuery.data?.data || []
  // Obtener datos extendidos: necesitamos hacer queries individuales o modificar el hook
  // Por ahora usamos los datos básicos y en el futuro el backend retornará extendido en la lista

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12} mb={2}>
        Bodegas
      </Heading>
      <Text mb={6} color="gray.600">
        Administra las instalaciones de almacenamiento
      </Text>

      {/* Stats Cards - Solo admin */}
      {isAdmin() && <StatsCards />}

      {/* Buscador y Filtros */}
      <Flex justify="space-between" align="center" mb={4} wrap="wrap" gap={4}>
        <Flex align="center" gap={4} flex={1} minW="300px">
          <InputGroup flex="1" startElement={<FiSearch />}>
            <Input
              placeholder="Buscar por nombre, tipo o ubicación..."
              size="sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </InputGroup>
          <select
            style={{
              width: "150px",
              height: "32px",
              padding: "4px 8px",
              fontSize: "14px",
              border: "1px solid #e2e8f0",
              borderRadius: "6px",
            }}
            value={filterTipo}
            onChange={(e) => setFilterTipo(e.target.value)}
          >
            <option value="">Todos los tipos</option>
            <option value="Principal">Principal</option>
            <option value="Secundaria">Secundaria</option>
            <option value="De tránsito">De tránsito</option>
          </select>
          {/* Filtro de sucursal - Solo admin puede cambiar */}
          {isAdmin() && alcance.sucursales.length > 0 && (
            <select
              style={{
                width: "200px",
                height: "32px",
                padding: "4px 8px",
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
          )}
          {/* No-admin: mostrar sucursal actual (readonly) */}
          {!isAdmin() && alcance.sucursales.length > 0 && (
            <select
              style={{
                width: "200px",
                height: "32px",
                padding: "4px 8px",
                fontSize: "14px",
                border: "1px solid #e2e8f0",
                borderRadius: "6px",
                backgroundColor: "#f7fafc",
                cursor: "not-allowed",
              }}
              value={alcance.scopeSucursalId || ""}
              disabled
            >
              {alcance.sucursales.map((sucursal) => (
                <option key={sucursal.id_sucursal} value={sucursal.id_sucursal}>
                  {sucursal.nombre}
                </option>
              ))}
            </select>
          )}
        </Flex>
        {/* Botón agregar - Solo admin */}
        {isAdmin() && <AddBodega />}
      </Flex>

      <Text fontSize="sm" color="gray.600" mb={4}>
        Lista de Bodegas
      </Text>

      {/* Lista de bodegas */}
      <BodegasList
        bodegas={bodegas}
        isLoading={bodegasQuery.isLoading}
      />
    </Container>
  )
}
