import { useQuery } from "@tanstack/react-query"
import { RolesService, SucursalesService } from "@/client"

/**
 * Hook para obtener roles y sucursales disponibles para la creación de usuarios
 */
export const useRolesAndSucursales = () => {
  // Fetch roles
  const {
    data: rolesData,
    isLoading: isLoadingRoles,
    error: rolesError,
    refetch: refetchRoles,
  } = useQuery({
    queryKey: ["roles"],
    queryFn: () => RolesService.readRoles({ skip: 0, limit: 100 }),
  })

  // Fetch sucursales
  const {
    data: sucursalesData,
    isLoading: isLoadingSucursales,
    error: sucursalesError,
    refetch: refetchSucursales,
  } = useQuery({
    queryKey: ["sucursales"],
    queryFn: () => SucursalesService.readSucursales({ skip: 0, limit: 100 }),
  })

  // Filtrar roles disponibles para creación de usuarios
  // Excluir Administrador (ID: 1) ya que solo se asigna automáticamente en signup
  const availableRoles = rolesData?.data?.filter((rol: { id_rol: number }) => rol.id_rol !== 1) || []

  // Normalizar sucursales (aceptar nombre_sucursal o nombre) y filtrar activas si estado !== false
  type RawSucursal = {
    id_sucursal: number
    nombre_sucursal?: string
    nombre?: string
    direccion?: string
    telefono?: string
    estado?: boolean
    fecha_creacion?: string
  }

  const normalizedSucursales = (sucursalesData?.data || []).map((s: RawSucursal) => ({
    id_sucursal: s.id_sucursal,
    nombre_sucursal: s.nombre_sucursal ?? s.nombre ?? "",
    direccion: s.direccion,
    telefono: s.telefono,
    estado: s.estado,
    fecha_creacion: s.fecha_creacion,
  }))

  const activeSucursales = normalizedSucursales.filter((s: { estado?: boolean }) => s.estado !== false)

  return {
    // Roles
    roles: availableRoles,
    isLoadingRoles,
    rolesError,
    refetchRoles,
    
    // Sucursales
    sucursales: activeSucursales,
    isLoadingSucursales,
    sucursalesError,
    refetchSucursales,
    
    // Estados combinados
    isLoading: isLoadingRoles || isLoadingSucursales,
    hasError: !!rolesError || !!sucursalesError,
  }
}
