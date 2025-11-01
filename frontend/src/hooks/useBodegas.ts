import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client"
import { request as apiRequest } from "@/client/core/request"
import useCustomToast from "./useCustomToast"
import { handleError } from "@/utils"
import { usePermissions } from "./usePermissions"

// Tipos para Bodega (basados en el backend)
export type BodegaPublic = {
  id_bodega: number
  nombre: string
  descripcion?: string | null
  tipo: string
  estado: boolean
  capacidad: number
  ubicacion?: string | null
  temperatura_min?: number | null
  temperatura_max?: number | null
  humedad_min?: number | null
  humedad_max?: number | null
  id_sucursal: number
}

export type BodegaPublicExtended = BodegaPublic & {
  total_lotes: number
  total_productos: number
  sucursal_nombre?: string | null
}

export type BodegasPublic = {
  data: BodegaPublic[]
  count: number
}

export type BodegaCreate = {
  nombre: string
  descripcion?: string | null
  tipo: string
  estado?: boolean
  capacidad: number
  ubicacion?: string | null
  temperatura_min?: number | null
  temperatura_max?: number | null
  humedad_min?: number | null
  humedad_max?: number | null
  id_sucursal: number
}

export type BodegaUpdate = {
  nombre?: string | null
  descripcion?: string | null
  tipo?: string | null
  estado?: boolean | null
  capacidad?: number | null
  ubicacion?: string | null
  temperatura_min?: number | null
  temperatura_max?: number | null
  humedad_min?: number | null
  humedad_max?: number | null
  id_sucursal?: number | null
}

export type BodegasStats = {
  total_bodegas: number
  operativas: number
  capacidad_total: number
  ocupacion_total: number
}

export const useBodegas = (params?: {
  q?: string | null
  tipo?: string | null
  estado?: boolean | null
  id_sucursal?: number | null
}) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const { isAdmin } = usePermissions()

  // Query para listar bodegas
  const bodegasQuery = useQuery({
    queryKey: [
      "bodegas",
      {
        q: params?.q || undefined,
        tipo: params?.tipo || undefined,
        estado: params?.estado,
        id_sucursal: params?.id_sucursal || undefined,
      },
    ],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: "/api/v1/bodegas/",
        query: {
          skip: 0,
          limit: 200,
          q: params?.q || undefined,
          tipo: params?.tipo || undefined,
          estado: params?.estado,
          id_sucursal: params?.id_sucursal || undefined,
        },
      }) as Promise<BodegasPublic>,
  })

  // Función helper para obtener query de bodega individual con datos extendidos
  const getBodegaQuery = (id: number) => ({
    queryKey: ["bodegas", id],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: `/api/v1/bodegas/${id}`,
      }) as Promise<BodegaPublicExtended>,
    enabled: !!id,
  })

  // Query para estadísticas - retorna objeto de query para usar con useQuery
  // Admin puede ver todas o filtrar por sucursal, no-admin solo ve su sucursal
  const getStatsQuery = (id_sucursal?: number | null) => ({
    queryKey: ["bodegas-stats", { id_sucursal }],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: "/api/v1/bodegas/stats",
        query: {
          id_sucursal: id_sucursal || undefined,
        },
      }) as Promise<BodegasStats>,
  })

  // Mantener compatibilidad con statsQuery (deprecated, usar getStatsQuery)
  const statsQuery = {
    queryKey: ["bodegas-stats"],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: "/api/v1/bodegas/stats",
      }) as Promise<BodegasStats>,
    enabled: isAdmin(),
  }

  // Mutation para crear bodega (solo admin)
  const createMutation = useMutation({
    mutationFn: (data: BodegaCreate) =>
      apiRequest(OpenAPI, {
        method: "POST",
        url: "/api/v1/bodegas/",
        body: data,
        mediaType: "application/json",
      }) as Promise<BodegaPublic>,
    onSuccess: () => {
      showSuccessToast("Bodega creada exitosamente")
      queryClient.invalidateQueries({ queryKey: ["bodegas"] })
      queryClient.invalidateQueries({ queryKey: ["bodegas-stats"] })
    },
    onError: handleError,
  })

  // Mutation para actualizar bodega
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: BodegaUpdate }) =>
      apiRequest(OpenAPI, {
        method: "PUT",
        url: `/api/v1/bodegas/${id}`,
        body: data,
        mediaType: "application/json",
      }) as Promise<BodegaPublic>,
    onSuccess: () => {
      showSuccessToast("Bodega actualizada exitosamente")
      queryClient.invalidateQueries({ queryKey: ["bodegas"] })
      queryClient.invalidateQueries({ queryKey: ["bodegas-stats"] })
    },
    onError: handleError,
  })

  // Mutation para eliminar bodega (soft delete)
  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(OpenAPI, {
        method: "DELETE",
        url: `/api/v1/bodegas/${id}`,
      }) as Promise<{ message: string }>,
    onSuccess: () => {
      showSuccessToast("Bodega eliminada exitosamente")
      queryClient.invalidateQueries({ queryKey: ["bodegas"] })
      queryClient.invalidateQueries({ queryKey: ["bodegas-stats"] })
    },
    onError: handleError,
  })

  return {
    bodegasQuery,
    getBodegaQuery,
    statsQuery,
    getStatsQuery,
    createMutation,
    updateMutation,
    deleteMutation,
  }
}

export default useBodegas

