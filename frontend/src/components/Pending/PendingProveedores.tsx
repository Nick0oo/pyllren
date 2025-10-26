import { Card, SkeletonText, SimpleGrid, Table } from "@chakra-ui/react"

const PendingProveedores = () => {
  return (
    <>
      {/* Stats Cards Skeleton */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
        {Array.from({ length: 4 }).map((_, index) => (
          <Card.Root key={index} p={4}>
            <Card.Body>
              <SkeletonText noOfLines={2} spacing="2" skeletonHeight="4" />
            </Card.Body>
          </Card.Root>
        ))}
      </SimpleGrid>

      {/* Table Skeleton */}
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
          {Array.from({ length: 5 }).map((_, index) => (
            <Table.Row key={index}>
              <Table.Cell>
                <SkeletonText noOfLines={2} spacing="1" skeletonHeight="3" />
              </Table.Cell>
              <Table.Cell>
                <SkeletonText noOfLines={1} skeletonHeight="3" />
              </Table.Cell>
              <Table.Cell>
                <SkeletonText noOfLines={1} skeletonHeight="3" />
              </Table.Cell>
              <Table.Cell>
                <SkeletonText noOfLines={2} spacing="1" skeletonHeight="3" />
              </Table.Cell>
              <Table.Cell>
                <SkeletonText noOfLines={1} skeletonHeight="3" />
              </Table.Cell>
              <Table.Cell>
                <SkeletonText noOfLines={1} skeletonHeight="3" />
              </Table.Cell>
              <Table.Cell>
                <SkeletonText noOfLines={1} skeletonHeight="3" />
              </Table.Cell>
              <Table.Cell>
                <SkeletonText noOfLines={1} skeletonHeight="3" />
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </>
  )
}

export default PendingProveedores
