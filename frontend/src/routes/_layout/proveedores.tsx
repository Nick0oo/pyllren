import {
  Badge,
  Card,
  Container,
  Flex,
  Heading,
  Input,
  SimpleGrid,
  Table,
  Text,
} from "@chakra-ui/react"
import { InputGroup } from "@/components/ui/input-group"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch, FiTruck, FiUsers, FiPackage, FiCalendar } from "react-icons/fi"
import { useState, useEffect } from "react"
import { z } from "zod"

import { ProveedoresService } from "@/client"
import AddProveedor from "@/components/Proveedores/AddProveedor"
import { ProveedorActionsMenu } from "@/components/Common/ProveedorActionsMenu"
import PendingProveedores from "@/components/Pending/PendingProveedores"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination"
import { usePermissions } from "@/hooks/usePermissions"

const proveedoresSearchSchema = z.object({
  page: z.number().catch(1),
  q: z.string().catch(""),
})

const PER_PAGE = 5

function getProveedoresQueryOptions({ page, q }: { page: number; q: string }) {
  return {
    queryFn: () =>
      ProveedoresService.readProveedores({ 
        skip: (page - 1) * PER_PAGE, 
        limit: PER_PAGE,
        q: q || undefined
      }),
    queryKey: ["proveedores", { page, q }],
  }
}

function getProveedoresStatsQueryOptions() {
  return {
    queryFn: () => ProveedoresService.getProveedoresStats(),
    queryKey: ["proveedores-stats"],
  }
}

export const Route = createFileRoute("/_layout/proveedores")({
  component: Proveedores,
  validateSearch: (search) => proveedoresSearchSchema.parse(search),
})

function StatsCards() {
  const { data: stats, isLoading } = useQuery(getProveedoresStatsQueryOptions())

  if (isLoading) {
    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
        {Array.from({ length: 4 }).map((_, index) => (
          <Card.Root key={index} p={4}>
            <Card.Body>
              <Text fontSize="sm" color="gray.500" mb={2}>
                Cargando...
              </Text>
              <Text fontSize="2xl" fontWeight="bold">
                --
              </Text>
            </Card.Body>
          </Card.Root>
        ))}
      </SimpleGrid>
    )
  }

  const statsData = [
    {
      title: "Total Proveedores",
      value: stats?.total_proveedores || 0,
      icon: FiUsers,
      color: "blue",
    },
    {
      title: "Activos",
      value: stats?.activos || 0,
      icon: FiTruck,
      color: "green",
    },
    {
      title: "Inactivos",
      value: stats?.inactivos || 0,
      icon: FiPackage,
      color: "gray",
    },
    {
      title: "Total Lotes",
      value: stats?.total_lotes || 0,
      icon: FiCalendar,
      color: "purple",
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
              <stat.icon fontSize="20px" color={`${stat.color}.500`} />
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

function ProveedoresTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page, q } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getProveedoresQueryOptions({ page, q }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      to: "/proveedores",
      search: (prev) => ({ ...prev, page }),
    })
  }

  const proveedores = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingProveedores />
  }

  return (
    <>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">Proveedores</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">NIT</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Contacto</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Comunicación</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Lotes</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Última entrega</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Estado</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Acciones</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {proveedores?.map((proveedor) => (
            <Table.Row key={proveedor.id_proveedor} opacity={isPlaceholderData ? 0.5 : 1}>
              <Table.Cell>
                <Text fontWeight="medium">{proveedor.nombre}</Text>
                <Text fontSize="sm" color="gray.500">
                  {proveedor.direccion}, {proveedor.ciudad}
                </Text>
              </Table.Cell>
              <Table.Cell truncate maxW="sm">
                {proveedor.nit}
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">{proveedor.telefono}</Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">{proveedor.email}</Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">-- Lotes</Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm">--</Text>
              </Table.Cell>
              <Table.Cell>
                <Badge colorPalette={proveedor.estado ? "green" : "gray"}>
                  {proveedor.estado ? "Activo" : "Inactivo"}
                </Badge>
              </Table.Cell>
              <Table.Cell>
                <ProveedorActionsMenu proveedor={proveedor} />
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
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
    </>
  )
}

function Proveedores() {
  const { canAccessModule } = usePermissions()
  const navigate = useNavigate()
  const { q } = Route.useSearch()
  const [searchTerm, setSearchTerm] = useState(q || "")

  // Debounce para la búsqueda
  useEffect(() => {
    const timer = setTimeout(() => {
      navigate({
        to: "/proveedores",
        search: (prev) => ({ ...prev, q: searchTerm, page: 1 }),
      })
    }, 500)

    return () => clearTimeout(timer)
  }, [searchTerm, navigate])

  // Verificar permisos de acceso
  if (!canAccessModule("admin")) {
    // Redirigir a home si no tiene permisos
    navigate({ to: "/" })
    return null
  }

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12} mb={6}>
        Proveedores
      </Heading>
      <Text mb={6} color="gray.600">
        Gestiona la información de tus proveedores
      </Text>

      <StatsCards />

      <Flex justify="space-between" align="center" mb={4}>
        <Flex align="center" gap={4}>
          <Text fontSize="sm" fontWeight="medium">
            Filtros de búsqueda
          </Text>
          <InputGroup flex="1" startElement={<FiSearch />} maxW="300px">
            <Input
              placeholder="Buscar por nombre, NIT o contacto..."
              size="sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </InputGroup>
        </Flex>
        <AddProveedor />
      </Flex>

      <Text fontSize="sm" color="gray.600" mb={4}>
        Lista de Proveedores
      </Text>

      <ProveedoresTable />
    </Container>
  )
}
