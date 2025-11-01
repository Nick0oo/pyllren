import { useQuery } from '@tanstack/react-query'
import { ProductosService } from '@/client/ProductosService'

export const getProductosQueryKey = (params: { skip?: number; limit?: number; q?: string } = {}) => ["productos", params]

export default function useProductos(params: { skip?: number; limit?: number; q?: string } = {}) {
  const { skip = 0, limit = 50, q } = params

  return useQuery({
    queryKey: getProductosQueryKey({ skip, limit, q }),
    queryFn: async () => {
      return await ProductosService.readProductos({ skip, limit, q })
    },
  })
}
