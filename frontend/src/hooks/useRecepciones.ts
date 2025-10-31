import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client"
import { request as apiRequest } from "@/client/core/request"
import useCustomToast from "./useCustomToast"
import { handleError } from "@/utils"

export type RecepcionProductoItem = {
  nombre_comercial: string
  nombre_generico?: string | null
  codigo_interno?: string | null
  codigo_barras?: string | null
  forma_farmaceutica: string
  concentracion: string
  presentacion: string
  unidad_medida: string
  cantidad: number
  stock_minimo: number
  stock_maximo: number
}

export type RecepcionLotePayload = {
  lote: {
    numero_lote?: string | null  // Opcional, se genera automáticamente en el backend
    fecha_fabricacion: string
    fecha_vencimiento: string
    estado: string
    observaciones?: string | null
    id_proveedor: number
    id_bodega: number | null
  }
  items: RecepcionProductoItem[]
}

export const useRecepciones = (params?: {
  id_bodega?: number | null
  id_sucursal?: number | null
  q?: string | null
}) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const lotesQuery = useQuery({
    queryKey: [
      "lotes",
      { q: params?.q || undefined, id_bodega: params?.id_bodega || undefined, id_sucursal: params?.id_sucursal || undefined },
    ],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: "/api/v1/lotes/",
        query: {
          skip: 0,
          limit: 50,
          q: params?.q || undefined,
          id_bodega: params?.id_bodega || undefined,
          id_sucursal: params?.id_sucursal || undefined,
        },
      }),
  })

  const recepcionMutation = useMutation({
    mutationFn: (data: RecepcionLotePayload) =>
      apiRequest(OpenAPI, {
        method: "POST",
        url: "/api/v1/lotes/recepcion",
        body: data,
        mediaType: "application/json",
      }),
    onSuccess: () => {
      showSuccessToast("Recepción registrada exitosamente")
      queryClient.invalidateQueries({ queryKey: ["lotes"] })
      queryClient.invalidateQueries({ queryKey: ["productos"] })
    },
    onError: handleError,
  })

  return {
    lotesQuery,
    recepcionMutation,
  }
}

export default useRecepciones


