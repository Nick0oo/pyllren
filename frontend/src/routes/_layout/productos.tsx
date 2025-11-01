
  import {
    Container,
    EmptyState,
    Flex,
    Box,
    Heading,
    Table,
    VStack,
    SimpleGrid,
    Text,
    Card,
    Icon,
  } from "@chakra-ui/react"
  import { useQuery } from "@tanstack/react-query"
  import { createFileRoute, useNavigate } from "@tanstack/react-router"
  import { FiSearch, FiBox, FiAlertTriangle } from "react-icons/fi"
  import { BsFillCircleFill } from "react-icons/bs"
  import { z } from "zod"

  import { ProductosService, type ProductoPublic, type ProductosStats } from "@/client/ProductosService"
  import { LotesService, type LotesStats } from "@/client/LotesService"
  import ProductoRow from "@/components/Productos/ProductoRow"
  import {
    PaginationItems,
    PaginationNextTrigger,
    PaginationPrevTrigger,
    PaginationRoot,
  } from "@/components/ui/pagination"
  import PendingItems from "@/components/Pending/PendingItems"
  import useAlcance from "@/hooks/useAlcance"
  import { usePermissions } from "@/hooks/usePermissions"

  const productosSearchSchema = z.object({
    page: z.number().catch(1),
    q: z.string().catch(""),
  })

  const PER_PAGE = 5

  function getProductosQueryOptions({ page, id_sucursal }: { page: number; id_sucursal?: number | null }) {
    return {
      queryFn: () => ProductosService.readProductos({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE, id_sucursal }),
      queryKey: ["productos", { page, id_sucursal }],
    }
  }

  export const Route = createFileRoute("/_layout/productos")({
    component: Productos,
    validateSearch: (search) => productosSearchSchema.parse(search),
  })

  function getProductosStatsQueryOptions(id_sucursal?: number | null) {
    return {
      queryFn: async () => {
        try {
          const response = await ProductosService.readStats({ id_sucursal })
          return response
        } catch (error) {
          console.error("Error in getProductosStats:", error)
          // Return safe defaults instead of throwing so UI can render fallback values
          return { total_productos: 0, stock_total: 0, lotes_activos: 0, productos_criticos: 0 }
        }
      },
      queryKey: ["productos-stats", { id_sucursal }],
      refetchOnWindowFocus: true,
      refetchInterval: 60000,
    }
  }

  function ProductosTable() {
    const navigate = useNavigate({ from: Route.fullPath })
    const { page } = Route.useSearch()
    const alcance = useAlcance()
    const { isAdmin } = usePermissions()

    // Get the effective id_sucursal for query
    const idSucursalQuery = isAdmin() ? alcance.scopeSucursalId : alcance.scopeSucursalId

    const { data, isLoading } = useQuery({
      ...getProductosQueryOptions({ page, id_sucursal: idSucursalQuery }),
      placeholderData: (prevData) => prevData,
    })

    const setPage = (p: number) => {
      navigate({ to: "/productos", search: (prev) => ({ ...prev, page: p }) })
    }

    const productos = data?.data ?? []
    const count = data?.count ?? 0

    if (isLoading) {
      return <PendingItems />
    }

    if (productos.length === 0) {
      return (
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiSearch />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>No se encontraron productos</EmptyState.Title>
              <EmptyState.Description>
                Aún no hay productos registrados en el sistema
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      )
    }

    return (
      <>
        <Table.Root size={{ base: "sm", md: "md" }}>
          <Table.Header>
            <Table.Row>
        <Table.ColumnHeader>producto</Table.ColumnHeader>
              <Table.ColumnHeader>concentración</Table.ColumnHeader>
              <Table.ColumnHeader>presentación</Table.ColumnHeader>
              <Table.ColumnHeader>forma</Table.ColumnHeader>
              <Table.ColumnHeader>stock</Table.ColumnHeader>
              <Table.ColumnHeader>Lote</Table.ColumnHeader>
              <Table.ColumnHeader>Bodega</Table.ColumnHeader>
        
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {productos.map((p: ProductoPublic) => (
              <ProductoRow key={p.id_producto} producto={p} />
            ))}
          </Table.Body>
        </Table.Root>

        <Flex justifyContent="flex-end" mt={4}>
          <PaginationRoot count={count} pageSize={PER_PAGE} onPageChange={({ page }) => setPage(page)}>
            <Flex>
              <PaginationPrevTrigger />
              <PaginationItems />
              <PaginationNextTrigger />
            </Flex>
          </PaginationRoot>
        </Flex>
      </>
    )
  }

  function StatsCards() {
    const alcance = useAlcance()
    const { isAdmin } = usePermissions()

    // Get the effective id_sucursal for queries
    const idSucursalQuery = isAdmin() ? alcance.scopeSucursalId : alcance.scopeSucursalId

    // Productos stats (primary source for product-centric cards)
    const { data: prodStats, isLoading: prodLoading, error: prodError } = useQuery<ProductosStats>(getProductosStatsQueryOptions(idSucursalQuery))

    // Also fetch lotes stats to get the canonical `activos` value (Lotes Activos)
    const { data: lotesStats, isLoading: lotesLoading, error: lotesError } = useQuery<LotesStats>({
      queryFn: async () => {
        try {
          return await LotesService.getLotesStats()
        } catch (err) {
          console.error("LotesService.getLotesStats failed:", err)
          // Return safe defaults to avoid throwing and to keep UI stable
          return { total_lotes: 0, activos: 0, vencidos: 0, proximos_a_vencer: 0 }
        }
      },
      queryKey: ["lotes-stats"],
      refetchOnWindowFocus: true,
      refetchInterval: 60000,
    })

    if (prodError) console.error("Error fetching productos stats:", prodError)
    if (lotesError) console.error("Error fetching lotes stats (for Lotes Activos):", lotesError)

    // Also fetch full productos list (to compute totals client-side) — limit large to get all
    const { data: allProds, isLoading: allLoading, error: allError } = useQuery({
      queryKey: ["productos-all", { id_sucursal: idSucursalQuery }],
      queryFn: () => ProductosService.readProductos({ skip: 0, limit: 10000, id_sucursal: idSucursalQuery }),
      staleTime: 60000,
    })

    if (allError) console.error("Error fetching all productos (for totals):", allError)

    const loading = prodLoading || lotesLoading || allLoading

    // compute derived totals from list when available
    const totalProductosFromList = allProds?.count ?? allProds?.data?.length ?? undefined
    const stockTotalFromList = allProds?.data ? allProds.data.reduce((s, p) => s + (p.cantidad_disponible ?? 0), 0) : undefined
    // Count productos críticos: cantidad_disponible <= stock_minimo
    const productosCriticosFromList = allProds?.data ? allProds.data.filter(p => p.cantidad_disponible <= p.stock_minimo).length : undefined

    const statsData = [
      {
        title: "Total Productos",
        // prefer client-side count from GET /productos, fallback to stats endpoint
        value: totalProductosFromList ?? prodStats?.total_productos ?? 0,
        icon: FiBox,
        color: "gray",
      },
      {
        title: "Stock Total",
        // prefer client-side sum, fallback to stats endpoint
        value: stockTotalFromList ?? prodStats?.stock_total ?? 0,
        icon: FiBox,
        color: "blue",
      },
      {
        title: "Lotes Activos",
        // Prefer the `activos` number from lotesStats (canonical). Fall back to producto.lotes_activos if available.
        value: lotesStats?.activos ?? prodStats?.lotes_activos ?? 0,
        icon: BsFillCircleFill,
        color: "green",
      },
      {
        title: "Productos Críticos",
        // prefer client-side count where cantidad_disponible <= stock_minimo, fallback to stats endpoint
        value: productosCriticosFromList ?? prodStats?.productos_criticos ?? 0,
        icon: FiAlertTriangle,
        color: "red",
      },
    ]

    if (loading) {
      return (
        <SimpleGrid columns={{ base: 1, md: 4 }} gap={4} mt={6}>
          {Array.from({ length: 4 }).map((_, index) => (
            <Card.Root key={index} p={4} borderWidth="1px" borderColor="gray.200">
              <Card.Body>
                <Flex align="center" justify="space-between" mb={2}>
                  <Text fontSize="sm" color="gray.500">Cargando...</Text>
                  <Icon as={FiBox} fontSize="20px" color="gray.300" />
                </Flex>
                <Text fontSize="2xl" fontWeight="bold" color="gray.300">--</Text>
              </Card.Body>
            </Card.Root>
          ))}
        </SimpleGrid>
      )
    }

    return (
      <SimpleGrid columns={{ base: 1, md: 4 }} gap={4} mt={6}>
        {statsData.map((stat, index) => (
          <Card.Root key={index} p={4} borderWidth="1px" borderColor="gray.200">
            <Card.Body>
              <Flex align="center" justify="space-between" mb={2}>
                <Text fontSize="sm" color="gray.500">{stat.title}</Text>
                <Icon as={stat.icon} fontSize="20px" color={`${stat.color}.500`} />
              </Flex>
              <Text fontSize="2xl" fontWeight="bold" color={`${stat.color}.600`}>{stat.value}</Text>
            </Card.Body>
          </Card.Root>
        ))}
      </SimpleGrid>
    )
  }

  export default function Productos() {
    return (
      <Container maxW="full">
        <Flex align="center" justify="space-between" pt={10}>
          <Box>
            <Heading size="4xl" fontWeight="bold">
              Gestión de productos
            </Heading>
            <Heading size="lg" fontWeight="semibold" mt={2}>
              Catálogo completo de medicamentos
            </Heading>
          </Box>
        </Flex>

        <StatsCards />



        <Box mt={8}>
          <ProductosTable />
        </Box>
      </Container>
    )
  }

