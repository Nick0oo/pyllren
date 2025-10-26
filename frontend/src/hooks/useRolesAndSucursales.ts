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
  } = useQuery({
    queryKey: ["roles"],
    queryFn: () => RolesService.readRoles({ skip: 0, limit: 100 }),
  })

  // Fetch sucursales
  const {
    data: sucursalesData,
    isLoading: isLoadingSucursales,
    error: sucursalesError,
  } = useQuery({
    queryKey: ["sucursales"],
    queryFn: () => SucursalesService.readSucursales({ skip: 0, limit: 100 }),
  })

  // Filtrar roles disponibles para creación de usuarios
  // Excluir Administrador (ID: 1) ya que solo se asigna automáticamente en signup
  const availableRoles = rolesData?.data?.filter(rol => rol.id_rol !== 1) || []

  // Filtrar sucursales activas
  const activeSucursales = sucursalesData?.data?.filter(sucursal => sucursal.estado) || []

  return {
    // Roles
    roles: availableRoles,
    isLoadingRoles,
    rolesError,
    
    // Sucursales
    sucursales: activeSucursales,
    isLoadingSucursales,
    sucursalesError,
    
    // Estados combinados
    isLoading: isLoadingRoles || isLoadingSucursales,
    hasError: !!rolesError || !!sucursalesError,
  }
}
