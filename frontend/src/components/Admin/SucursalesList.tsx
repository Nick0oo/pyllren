import { Container, Flex, Heading, Table } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { SucursalesService } from "@/client"
import AddSucursal from "@/components/Admin/AddSucursal"
import EditSucursal from "@/components/Admin/EditSucursal"
import DeleteSucursal from "@/components/Admin/DeleteSucursal"
import PendingUsers from "@/components/Pending/PendingUsers"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"

const PER_PAGE = 5

export default function SucursalesList() {
  const [page, setPage] = useState(1)

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ["sucursales", { page }],
    queryFn: () => SucursalesService.readSucursales({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    placeholderData: (prev) => prev,
  })

  const sucursales = data?.data ?? []
  const count = data?.count ?? 0

  if (isLoading) return <PendingUsers />

  return (
    <Container maxW="full" px={0}>
      <Flex justify="space-between" align="center" mb={3} mt={8}>
        <Heading size="md">Sucursales</Heading>
        <AddSucursal />
      </Flex>

      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">Nombre</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Dirección</Table.ColumnHeader>
            <Table.ColumnHeader w="xs">Teléfono</Table.ColumnHeader>
            <Table.ColumnHeader w="xs">Estado</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Creada</Table.ColumnHeader>
            <Table.ColumnHeader w="xs">Acciones</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {sucursales.map((s: any) => {
            const nombre = s.nombre_sucursal ?? s.nombre ?? ""
            return (
            <Table.Row key={s.id_sucursal} opacity={isPlaceholderData ? 0.5 : 1}>
              <Table.Cell>{nombre}</Table.Cell>
              <Table.Cell truncate maxW="md">{s.direccion}</Table.Cell>
              <Table.Cell>{s.telefono}</Table.Cell>
              <Table.Cell>{s.estado ? "Activa" : "Inactiva"}</Table.Cell>
              <Table.Cell>{new Date(s.fecha_creacion as unknown as string).toLocaleDateString()}</Table.Cell>
              <Table.Cell>
                <Flex gap={2}>
                  <EditSucursal sucursal={s as any} />
                  <DeleteSucursal sucursal={s as any} />
                </Flex>
              </Table.Cell>
            </Table.Row>
          )})}
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
    </Container>
  )
}


