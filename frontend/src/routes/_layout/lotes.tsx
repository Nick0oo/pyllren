import {
  Badge,
  Button,
  Card,
  Container,
  EmptyState,
  Flex,
  Heading,
  Icon,
  Input,
  SimpleGrid,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiPackage, FiAlertTriangle, FiSearch } from "react-icons/fi"
import { useState, useEffect } from "react"
import { z } from "zod"

import { LotesService, BodegasService, type LotePublic, type LotesStats, type BodegaPublic } from "@/client"

import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination"
import { BsFillCircleFill } from "react-icons/bs"
import { Select, SelectItem } from "@/components/ui/select"

const lotesSearchSchema = z.object({
  page: z.number().catch(1),
  q: z.string().catch(""),
  estado: z.string().catch(""),
  id_bodega: z.string().catch(""),
})

const PER_PAGE = 5

function getLotesQueryOptions({ 
  page, 
  q, 
  estado, 
  id_bodega 
}: { 
  page: number
  q: string
  estado: string
  id_bodega: string
}) {
  return {
    queryFn: () =>
      LotesService.readLotes({
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
        q: q || undefined,
        estado: estado && estado !== "" ? estado : undefined,
        id_bodega: id_bodega && id_bodega !== "" ? Number(id_bodega) : undefined,
      }),
    queryKey: ["lotes", { page, q, estado, id_bodega }],
  }
}

function getLotesStatsQueryOptions() {
  return {
    queryFn: () => LotesService.getLotesStats(),
    queryKey: ["lotes-stats"],
  }
}

export const Route = createFileRoute("/_layout/lotes")({
  component: Lotes,
  validateSearch: (search) => lotesSearchSchema.parse(search),
})

function StatsCards() {
  const { data: stats } = useQuery<LotesStats>(getLotesStatsQueryOptions())
  const statsData = [
    {
      title: "Total Lotes",
      value: stats?.total_lotes || 0,
      icon: FiPackage,
      color: "gray",
    },
    {
      title: "Lotes Activos",
      value: stats?.activos || 0,
      icon: BsFillCircleFill,
      color: "green",
    },
    {
      title: "Vencidos",
      value: stats?.vencidos || 0,
      icon: FiAlertTriangle,
      fill: "red",
      color: "red",
    },
    {
      title: "Próximos a vencer",
      value: stats?.próximos_a_vencer || 0,
      icon: FiAlertTriangle,
      fill: "yellow",
      color: "yellow",
    },  
  ]

  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
      {statsData.map((stat, index) => (
        <Card.Root key={index} p={4}>
          <Card.Body>
            <Flex align="center" justify="space-between" mb={2}>
              <Text fontSize="sm" color="gray.500">
                {stat.title}
              </Text>
              <Icon as={stat.icon} fontSize="20px" color={`${stat.color}.500`} />
            </Flex>
            <Text fontSize="2xl" fontWeight="bold" color={`${stat.color}.600`}>
              {stat.value}
            </Text>
          </Card.Body>
        </Card.Root>
      ))}
    </SimpleGrid>
  )
}

function LotesTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page, q, estado, id_bodega } = Route.useSearch()

  // Convertir "Próximos a vencer" - esto necesita un manejo especial
  // Por ahora, si es "Próximos a vencer", no pasamos estado y filtramos después
  const estadoParam = estado === "Próximos a vencer" ? "" : (estado || "")

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getLotesQueryOptions({ 
      page, 
      q: q || "", 
      estado: estadoParam, 
      id_bodega: id_bodega || ""
    }),
    placeholderData: (prevData) => prevData,
  })

  let lotes: LotePublic[] = data?.data ?? []
  let count = data?.count ?? 0

  // Filtro especial para "Próximos a vencer" (mejor hacerlo en backend, pero por ahora en frontend)
  if (estado === "Próximos a vencer") {
    lotes = lotes.filter((lote) => {
      const fechaVencimiento = new Date(lote.fecha_vencimiento)
      const hoy = new Date()
      const diffTime = fechaVencimiento.getTime() - hoy.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return diffDays > 0 && diffDays <= 30 && lote.estado === "Activo"
    })
    count = lotes.length
  }

  const setPage = (newPage: number) => {
    navigate({
      to: "/lotes",
      search: (prev) => ({ ...prev, page: newPage }),
    })
  }

  if (isLoading && !isPlaceholderData) {
    return (
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">Lotes</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Producto</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Fecha de Vencimiento</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Stock</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Proveedor</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Bodega</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Estado</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Acciones</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {Array.from({ length: PER_PAGE }).map((_, i) => (
            <Table.Row key={i}>
              <Table.Cell>...</Table.Cell>
              <Table.Cell>...</Table.Cell>
              <Table.Cell>...</Table.Cell>
              <Table.Cell>...</Table.Cell>
              <Table.Cell>...</Table.Cell>
              <Table.Cell>...</Table.Cell>
              <Table.Cell>...</Table.Cell>
              <Table.Cell>...</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    )
  }

  return (
    <>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">Lotes</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Producto</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Fecha de Vencimiento</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Stock</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Proveedor</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Bodega</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Estado</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Acciones</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {lotes?.map((lote: LotePublic) => (
            <Table.Row key={lote.id_lote} opacity={isPlaceholderData ? 0.5 : 1}>
              <Table.Cell>
                <Text fontWeight="medium">{lote.numero_lote}</Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">--</Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">
                  {new Date(lote.fecha_vencimiento).toLocaleDateString()}
                </Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">--</Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">{lote.id_proveedor}</Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">{lote.id_bodega}</Text>
              </Table.Cell>
              <Table.Cell>
                <Badge
                  colorPalette={
                    lote.estado === "Activo"
                      ? "green"
                      : lote.estado === "Vencido"
                      ? "red"
                      : lote.estado === "En tránsito"
                      ? "blue"
                      : "orange"
                  }
                >
                  {lote.estado}
                </Badge>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">--</Text>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
      {lotes.length === 0 && !isLoading && (
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiSearch />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>No se encontraron lotes</EmptyState.Title>
              <EmptyState.Description>
                {q || estado || id_bodega
                  ? "Intenta ajustar los filtros de búsqueda"
                  : "Aún no hay lotes registrados en el sistema"}
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      )}
      {count > 0 && (
        <Flex justifyContent="flex-end" mt={4}>
          <PaginationRoot
            count={count}
            pageSize={PER_PAGE}
            onPageChange={({ page }) => setPage(page)}
          >
            <Flex>
              <PaginationPrevTrigger />
              <PaginationItems />
              <PaginationNextTrigger />
            </Flex>
          </PaginationRoot>
        </Flex>
      )}
    </>
  )
}

function Lotes() {
  const navigate = useNavigate()
  const { page, q, estado, id_bodega } = Route.useSearch()
  const [searchQuery, setSearchQuery] = useState<string>(q || "")
  const [estadoFilter, setEstadoFilter] = useState<string>(estado || "")
  const [filterBodega, setFilterBodega] = useState<string>(id_bodega || "")

  // Sincronizar estados locales con URL cuando cambien los parámetros
  useEffect(() => {
    setSearchQuery(q || "")
    setEstadoFilter(estado || "")
    setFilterBodega(id_bodega || "")
  }, [q, estado, id_bodega])

  // Debounce para la búsqueda - actualiza URL después de 500ms
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery !== (q || "")) {
        navigate({
          to: "/lotes",
          search: {
            page: 1,
            q: searchQuery || "",
            estado: estadoFilter || "",
            id_bodega: filterBodega || "",
          },
        })
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [searchQuery]) // eslint-disable-line react-hooks/exhaustive-deps

  // Actualizar URL cuando cambie el filtro de estado
  useEffect(() => {
    if (estadoFilter !== (estado || "")) {
      navigate({
        to: "/lotes",
        search: {
          page: 1,
          q: searchQuery || "",
          estado: estadoFilter || "",
          id_bodega: filterBodega || "",
        },
      })
    }
  }, [estadoFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  // Actualizar URL cuando cambie el filtro de bodega
  useEffect(() => {
    if (filterBodega !== (id_bodega || "")) {
      navigate({
        to: "/lotes",
        search: {
          page: 1,
          q: searchQuery || "",
          estado: estadoFilter || "",
          id_bodega: filterBodega || "",
        },
      })
    }
  }, [filterBodega]) // eslint-disable-line react-hooks/exhaustive-deps

  // Obtener las bodegas para el select
  const { data: bodegasData } = useQuery({
    queryFn: () => BodegasService.readBodegas({ skip: 0, limit: 1000 }),
    queryKey: ["bodegas"],
  })

  const bodegasActivas = bodegasData?.data?.filter((bodega: BodegaPublic) => bodega.estado) || []

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12} mb={6}>
          Gestión de lotes
      </Heading>
      <Text mb={6} color="gray.600">
        Gestiona la información de tus lotes
      </Text>

      <StatsCards />
      <Text fontSize="lg" fontWeight="medium">
          Filtros de búsqueda
          </Text>
      <Flex justify="space-between" align="center" mb={4}>
        <Flex align="center" gap={4}>
          <Input
            placeholder="Buscar por número de lote..."
            size="sm"
            maxW="300px"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Select
            placeholder="Filtrar por estado"
            value={estadoFilter}
            onValueChange={(value) => setEstadoFilter(value)}
            style={{ maxWidth: "300px",  color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
          >
            <SelectItem value="">Todos los estados</SelectItem>
            <SelectItem value="Activo">Activo</SelectItem>
            <SelectItem value="Vencido">Vencido</SelectItem>
            <SelectItem value="Próximos a vencer">Próximos a vencer</SelectItem>
          </Select>
          <Select
            placeholder={bodegasActivas.length === 0 ? "No hay bodegas" : "Filtrar por Bodega"}
            value={bodegasActivas.length === 0 ? "" : filterBodega}
            onValueChange={(value) => setFilterBodega(value)}
            disabled={bodegasActivas.length === 0}
            style={{ maxWidth: "300px",  color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
          >
            {bodegasActivas.length === 0 ? (
              <SelectItem value="" disabled>
                No hay bodegas
              </SelectItem>
            ) : (
              <>
                <SelectItem value="">Todas las bodegas</SelectItem>
                {bodegasActivas.map((bodega: BodegaPublic) => (
                  <SelectItem key={bodega.id_bodega} value={String(bodega.id_bodega)}>
                    {bodega.nombre}
                  </SelectItem>
                ))}
              </>
            )}
          </Select>
          <Button
            variant="subtle"
            colorPalette="gray"
            onClick={() => {
              setSearchQuery("")
              setEstadoFilter("")
              setFilterBodega("")
              navigate({
                to: "/lotes",
                search: { page: 1, q: "", estado: "", id_bodega: "" },
              })
            }}
          >
            Limpiar filtros
          </Button>
        </Flex>
      </Flex>
      <LotesTable />
    </Container>
  )
}