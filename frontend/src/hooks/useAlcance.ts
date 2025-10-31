import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { OpenAPI } from "@/client"
import { request as apiRequest } from "@/client/core/request"
import { usePermissions } from "./usePermissions"

type Sucursal = {
  id_sucursal: number
  nombre?: string
  nombre_sucursal?: string
}

type Bodega = {
  id_bodega: number
  id_sucursal: number
  nombre: string
}

export const useAlcance = () => {
  const { currentUser, isAdmin } = usePermissions()
  const [adminSucursalId, setAdminSucursalId] = useState<number | null>(null)

  const scopeSucursalId = isAdmin() ? adminSucursalId : currentUser?.id_sucursal ?? null

  const sucursalesQuery = useQuery<{ data: Sucursal[]; count: number }>({
    queryKey: ["sucursales"],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: "/api/v1/sucursales/",
        query: { skip: 0, limit: 200 },
      }),
    enabled: isAdmin(),
  })

  // Query para obtener la sucursal del usuario no-admin
  const userSucursalQuery = useQuery<{ id_sucursal: number; nombre_sucursal?: string; nombre?: string }>({
    queryKey: ["sucursales", currentUser?.id_sucursal],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: `/api/v1/sucursales/${currentUser?.id_sucursal}`,
      }),
    enabled: !isAdmin() && !!currentUser?.id_sucursal,
  })

  const bodegasQuery = useQuery<{ data: Bodega[]; count: number }>({
    queryKey: ["bodegas", { id_sucursal: scopeSucursalId, isAdmin: isAdmin() }],
    queryFn: () =>
      apiRequest(OpenAPI, {
        method: "GET",
        url: "/api/v1/bodegas/",
        query: { skip: 0, limit: 200 },
      }),
    // El backend ya filtra por alcance, así que siempre podemos hacer la query
  })

  const sucursales = useMemo(() => {
    if (isAdmin()) {
      const list = sucursalesQuery.data?.data || []
      return list.map((s) => ({
        id_sucursal: s.id_sucursal,
        nombre: s.nombre_sucursal ?? s.nombre ?? `Sucursal ${s.id_sucursal}`,
      }))
    }
    // Para usuarios no-admin, incluir su sucursal en la lista
    if (currentUser?.id_sucursal && userSucursalQuery.data) {
      return [{
        id_sucursal: userSucursalQuery.data.id_sucursal,
        nombre: userSucursalQuery.data.nombre_sucursal ?? userSucursalQuery.data.nombre ?? `Sucursal ${currentUser.id_sucursal}`,
      }]
    }
    // Fallback si aún no se ha cargado la sucursal
    if (currentUser?.id_sucursal) {
      return [{
        id_sucursal: currentUser.id_sucursal,
        nombre: `Sucursal ${currentUser.id_sucursal}`,
      }]
    }
    return []
  }, [sucursalesQuery.data, isAdmin, currentUser, userSucursalQuery.data])

  return {
    isAdmin: isAdmin(),
    scopeSucursalId,
    setAdminSucursalId,
    sucursales,
    bodegas: bodegasQuery.data?.data || [],
    isLoading: sucursalesQuery.isLoading || bodegasQuery.isLoading || userSucursalQuery.isLoading,
  }
}

export default useAlcance


