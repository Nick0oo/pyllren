import { Table, Text, Badge } from '@chakra-ui/react'
import type { ProductoPublic } from '@/client/ProductosService'

export default function ProductoRow({ producto }: { producto: ProductoPublic }) {
  return (
    <Table.Row>
        <Table.Cell>
          <Text fontWeight="semibold">{producto.nombre_comercial}</Text>
        </Table.Cell>
        <Table.Cell>{producto.concentracion}</Table.Cell>
        <Table.Cell>{producto.presentacion}</Table.Cell>
        <Table.Cell>{producto.forma_farmaceutica}</Table.Cell>
        <Table.Cell>{producto.cantidad_disponible}</Table.Cell>
        <Table.Cell>{producto.numero_lote ?? producto.id_lote ?? '—'}</Table.Cell>
        <Table.Cell>
          <Badge colorScheme={producto.bodega_nombre ? 'green' : 'gray'}>
            {producto.bodega_nombre ?? 'Sin bodega'}
          </Badge>
        </Table.Cell>
      </Table.Row>
  )
}
