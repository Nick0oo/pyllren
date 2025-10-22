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
  
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState, useRef, useEffect } from "react"
import { createPortal } from "react-dom"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { FiSearch } from "react-icons/fi"
import { z } from "zod"
import { FiBox } from "react-icons/fi";


import { ItemsService } from "@/client"
import { ItemActionsMenu } from "@/components/Common/ItemActionsMenu"
import AddItem from "@/components/Items/AddItem"
import PendingItems from "@/components/Pending/PendingItems"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"

const itemsSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 5

function getItemsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      ItemsService.readItems({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["items", { page }],
  }
}

export const Route = createFileRoute("/_layout/items")({
  component: Items,
  validateSearch: (search) => itemsSearchSchema.parse(search),
})

function ItemsTable() {
  const navigate = useNavigate({ from: Route.fullPath })
  const { page } = Route.useSearch()

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getItemsQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const setPage = (page: number) => {
    navigate({
      to: "/items",
      search: (prev) => ({ ...prev, page }),
    })
  }

  const items = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingItems />
  }

  if (items.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>No tienes elementos todavía</EmptyState.Title>
            <EmptyState.Description>
              Agrega un nuevo elemento para empezar
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
            <Table.ColumnHeader w="sm">código</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">producto</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">concentración</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">presentación</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">categoría</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Lotes activos</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">stock</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">estado</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Acciones</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {items?.map((item) => (
            <Table.Row key={item.id} opacity={isPlaceholderData ? 0.5 : 1}>
              <CodeCell id={item.id} />
              <Table.Cell truncate maxW="sm">{item.title || ""}</Table.Cell>
              <Table.Cell truncate maxW="sm">{(item as any).concentration || ""}</Table.Cell>
              <Table.Cell truncate maxW="sm">{(item as any).presentation || ""}</Table.Cell>
              <Table.Cell truncate maxW="sm">{(item as any).category || ""}</Table.Cell>
              <Table.Cell truncate maxW="sm">{(item as any).active_lots ?? (item as any).lotes_activos ?? ""}</Table.Cell>
              <Table.Cell truncate maxW="sm">{(item as any).stock ?? ""}</Table.Cell>
              <Table.Cell truncate maxW="sm">{(item as any).status || (item as any).estado || ""}</Table.Cell>
              <Table.Cell>
                <ItemActionsMenu item={item} />
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

// Component that shows a truncated id (4 chars) with Tooltip on hover and Popover on double click
function CodeCell({ id }: { id?: string }) {
  const [showOverlay, setShowOverlay] = useState(false)
  const [coords, setCoords] = useState<{ x: number; y: number } | null>(null)
  const elRef = useRef<HTMLDivElement | null>(null)
  const display = id ? String(id).slice(0, 4) : ""

  useEffect(() => {
    if (!showOverlay) return
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setShowOverlay(false)
    }
    function onClick(e: MouseEvent) {
      // close when clicking outside overlay
      const target = e.target as Node
      if (elRef.current && !elRef.current.contains(target as Node)) {
        setShowOverlay(false)
      }
    }
    window.addEventListener("keydown", onKey)
    window.addEventListener("mousedown", onClick)
    return () => {
      window.removeEventListener("keydown", onKey)
      window.removeEventListener("mousedown", onClick)
    }
  }, [showOverlay])

  function openOverlay() {
    if (!elRef.current) return setShowOverlay(true)
    const rect = elRef.current.getBoundingClientRect()
    // position above the element, centered
    setCoords({ x: rect.left + rect.width / 2, y: rect.top })
    setShowOverlay(true)
  }

  return (
    <>
      <Table.Cell truncate maxW="sm">
        <Box
          ref={elRef}
          title={id}
          onDoubleClick={openOverlay}
          cursor={id ? "pointer" : "default"}
        >
          {display}
        </Box>
      </Table.Cell>

      {showOverlay && coords
        ? createPortal(
            <Box
              position="fixed"
              left={`${coords.x}px`}
              top={`${coords.y - 28}px`}
              transform="translateX(-50%)"
              bg="gray.800"
              color="white"
              px={3}
              py={1}
              rounded="md"
              zIndex={9999}
              onDoubleClick={() => setShowOverlay(false)}
            >
              {id}
            </Box>,
            document.body,
          )
        : null}
    </>
  )
}

function Items() {
  return (
    <Container maxW="full">
      <Flex align="center" justify="space-between" pt={10}>
        <Box>
          <Heading size="4xl" fontWeight="bold">
            Gestión de productos
          </Heading>
          <Heading size="lg" fontWeight="semibold" mt={2}>
            Administra tus productos de manera eficiente
          </Heading>
        </Box>
        <AddItem />
      </Flex>


        {/* Cards métricas "Aquí van los endpoints de metrics" */}

   
    <SimpleGrid columns={{ base: 1, md: 4 }} gap={4} mt={6}>

          <Box borderWidth="1px" borderColor="gray.200" rounded="md" p={6}>
            <Flex justify={"space-between"}>
              <Text fontSize="sm" fontWeight="semibold">Total Productos</Text>
              <FiBox size="25px" color="#31c89d"/>
            </Flex>
            <Heading size="lg" mt={2}>0</Heading>
            <Text fontSize="xs"  mt={1}>productos registrados</Text>
          </Box>

          <Box borderWidth="1px" borderColor="gray.200" rounded="md" p={6}>
            <Flex justify={"space-between"}>
              <Text fontSize="sm" fontWeight="semibold">Stock Total</Text>
              <FiBox size="25px" color="blue"/>
            </Flex>
            <Heading size="lg" mt={2}>0</Heading>
            <Text fontSize="xs"  mt={1}>unidades en stock</Text>
          </Box>

          <Box borderWidth="1px" borderColor="gray.200" rounded="md" p={6}>
            <Flex justify={"space-between"}>
              <Text fontSize="sm" fontWeight="semibold">Lotes Activos</Text>
              <FiBox size="25px" color="orange"/>
            </Flex>
            <Heading size="lg" mt={2}>0</Heading>
            <Text fontSize="xs"  mt={1}>lotes disponibles</Text>
          </Box>

          <Box borderWidth="1px" borderColor="gray.200" rounded="md" p={6}>
            <Flex justify={"space-between"}>
              <Text fontSize="sm" fontWeight="semibold">Productos Críticos</Text>
              <FiBox size="25px" />
            </Flex>
            <Heading size="lg" mt={2}>0</Heading>
            <Text fontSize="xs" mt={1}>requieren atención</Text>
          </Box>
        </SimpleGrid>
    
        <Text fontSize="sm" color="gray.500" mt={2}>
          GET: Obtiene los 4 contadores principales: Total Productos, Stock Total, Lotes Activos y Productos Críticos.
        </Text>
        <Box mt={8}>
          <ItemsTable />
        </Box>
    </Container>
  )
}
