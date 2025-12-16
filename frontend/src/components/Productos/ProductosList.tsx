import {
  Badge,
  Button,
  Container,
  Flex,
  Heading,
  Input,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"
import ProductoRow from "./ProductoRow"
import { ProductosService } from "@/client/ProductosService"
import { BodegasService, type BodegaPublic } from "@/client"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination"
import { EmptyState } from "@chakra-ui/react"
import { Select, SelectItem } from "../ui/select"

const productosSearchSchema = z.object({
  page: z.number().catch(1),
  q: z.string().catch("")
})

const PER_PAGE = 5

function getProductosQueryOptions({ page, q }: { page: number; q: string }) {
  return {
    queryFn: () =>
      ProductosService.readProductos({
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
        q: q || undefined,
      }),
    queryKey: ["productos", { page, q }],
  }
}

export const Route = createFileRoute("/_layout/productos")({
  component: ProductosList,
  validateSearch: (s) => productosSearchSchema.parse(s),
})

export default function ProductosList() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page, q } = Route.useSearch()
  const [searchQuery, setSearchQuery] = (q != null) ? [q, (v: string) => navigate({ to: "/productos", search: { page: 1, q: v }})] : ["", (v: string) => navigate({ to: "/productos", search: { page: 1, q: v }})]

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getProductosQueryOptions({ page: page || 1, q: q || "" }),
    placeholderData: (prev) => prev,
  })

  const productos = data?.data ?? []
  const count = data?.count ?? 0

  // Bodegas for filter (optional)
  const { data: bodegasData } = useQuery({
    queryFn: () => BodegasService.readBodegas({ skip: 0, limit: 1000 }),
    queryKey: ["bodegas"],
  })

  const bodegas = bodegasData?.data ?? []

  const setPage = (newPage: number) => {
    navigate({ to: "/productos", search: (prev) => ({ ...prev, page: newPage }) })
  }

  return (
    <Container maxW="full">
      <Heading size="lg" pt={8} mb={2}>
        Gestión de productos
      </Heading>
      <Text mb={6} color="gray.600">
        Catálogo completo de medicamentos
      </Text>

      <Text fontSize="lg" fontWeight="medium">
        Lista de productos
      </Text>

      <Flex justify="space-between" align="center" mb={4} mt={4}>
        <Flex align="center" gap={4}>
          <Input
            placeholder="Buscar por nombre o código..."
            size="sm"
            maxW="360px"
            value={q || ""}
            onChange={(e) => {
              const v = e.target.value
              // debounce-like behavior: navigate will update URL
              navigate({ to: "/productos", search: { page: 1, q: v } })
            }}
          />
          <Select placeholder="todas las categorías" style={{ maxWidth: "200px" }}>
            <SelectItem value="">todas las categorías</SelectItem>
          </Select>
        </Flex>
      </Flex>

      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">Código</Table.ColumnHeader>
            <Table.ColumnHeader>Producto</Table.ColumnHeader>
            <Table.ColumnHeader>Concentración</Table.ColumnHeader>
            <Table.ColumnHeader>Presentación</Table.ColumnHeader>
            <Table.ColumnHeader>Forma</Table.ColumnHeader>
            <Table.ColumnHeader>Stock</Table.ColumnHeader>
            <Table.ColumnHeader>Lote</Table.ColumnHeader>
            <Table.ColumnHeader>Bodega</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {productos.map((p) => (
            <ProductoRow key={p.id_producto} producto={p} />
          ))}
        </Table.Body>
      </Table.Root>

      {productos.length === 0 && !isLoading && (
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiSearch />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>No se encontraron productos</EmptyState.Title>
              <EmptyState.Description>
                {q ? "Intenta ajustar los filtros de búsqueda" : "Aún no hay productos registrados"}
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      )}

      {count > 0 && (
        <Flex justifyContent="flex-end" mt={4}>
          <PaginationRoot count={count} pageSize={PER_PAGE} onPageChange={({ page }) => setPage(page)}>
            <Flex>
              <PaginationPrevTrigger />
              <PaginationItems />
              <PaginationNextTrigger />
            </Flex>
          </PaginationRoot>
        </Flex>
      )}
    </Container>
  )
}
