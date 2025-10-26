import { useQueryClient } from "@tanstack/react-query"
import type { UserPublic } from "@/client"

// Constantes de roles basadas en la BD
export const ROLES = {
  ADMINISTRADOR: 1,
  FARMACEUTICO: 2,
  AUXILIAR: 3,
  AUDITOR: 4,
} as const

export const ROLE_NAMES = {
  [ROLES.ADMINISTRADOR]: "Administrador",
  [ROLES.FARMACEUTICO]: "Farmacéutico", 
  [ROLES.AUXILIAR]: "Auxiliar",
  [ROLES.AUDITOR]: "Auditor",
} as const

export type RoleId = typeof ROLES[keyof typeof ROLES]

/**
 * Hook para manejar permisos basados en roles
 */
export const usePermissions = () => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])

  /**
   * Verifica si el usuario actual es administrador
   */
  const isAdmin = (): boolean => {
    if (!currentUser) return false
    return currentUser.id_rol === ROLES.ADMINISTRADOR || currentUser.is_superuser === true
  }

  /**
   * Verifica si el usuario actual tiene un rol específico
   */
  const hasRole = (roleId: RoleId): boolean => {
    if (!currentUser) return false
    return currentUser.id_rol === roleId
  }

  /**
   * Verifica si el usuario puede acceder a un módulo específico
   */
  const canAccessModule = (module: string): boolean => {
    if (!currentUser) return false

    switch (module) {
      case "admin":
        return isAdmin()
      case "inventory":
        return hasRole(ROLES.ADMINISTRADOR) || hasRole(ROLES.FARMACEUTICO) || hasRole(ROLES.AUXILIAR)
      case "audit":
        return hasRole(ROLES.ADMINISTRADOR) || hasRole(ROLES.AUDITOR)
      default:
        return false
    }
  }

  /**
   * Obtiene el nombre del rol del usuario actual
   */
  const getCurrentUserRoleName = (): string => {
    if (!currentUser) return "Sin rol"
    if (currentUser.is_superuser) return "Superusuario"
    if (currentUser.id_rol) {
      return ROLE_NAMES[currentUser.id_rol as RoleId] || "Rol desconocido"
    }
    return "Sin rol"
  }

  /**
   * Verifica si el usuario tiene permisos de superusuario
   */
  const isSuperUser = (): boolean => {
    return currentUser?.is_superuser === true
  }

  return {
    currentUser,
    isAdmin,
    hasRole,
    canAccessModule,
    getCurrentUserRoleName,
    isSuperUser,
    ROLES,
    ROLE_NAMES,
  }
}
