import { Box, Flex, Icon, Text } from "@chakra-ui/react"
import { Link as RouterLink } from "@tanstack/react-router"
import { FiBriefcase, FiHome, FiSettings, FiUsers, FiTruck, FiPackage, FiBox } from "react-icons/fi"
import type { IconType } from "react-icons/lib"

import { usePermissions } from "@/hooks/usePermissions"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  // Punto de entrada para la gestión de productos (lee desde /productos)
  { icon: FiBriefcase, title: "Productos", path: "/productos" },
  { icon: FiSettings, title: "Configuración de usuario", path: "/settings" },
  { icon: FiPackage, title: "Lotes", path: "/lotes" },
]

interface SidebarItemsProps {
  onClose?: () => void
}

interface Item {
  icon: IconType
  title: string
  path: string
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const { canAccessModule } = usePermissions()

  const adminItems: Item[] = [
    { icon: FiUsers, title: "Admin", path: "/admin" },
    { icon: FiTruck, title: "Proveedores", path: "/proveedores" },
    { icon: FiBox, title: "Bodegas", path: "/bodegas" },
  ]

  const inventoryItems: Item[] = [
    { icon: FiPackage, title: "Recepción de lotes", path: "/recepciones" },
  ]

  const finalItems: Item[] = [
    ...items,
    ...(canAccessModule("inventory") ? inventoryItems : []),
    ...(canAccessModule("admin") ? adminItems : []),
  ]

  const listItems = finalItems.map(({ icon, title, path }) => (
    <RouterLink key={title} to={path} onClick={onClose}>
      <Flex
        gap={4}
        px={4}
        py={2}
        _hover={{
          background: "gray.subtle",
        }}
        alignItems="center"
        fontSize="sm"
      >
        <Icon as={icon} alignSelf="center" />
        <Text ml={2}>{title}</Text>
      </Flex>
    </RouterLink>
  ))

  return (
    <>
      <Text fontSize="xs" px={4} py={2} fontWeight="bold">
        Menu
      </Text>
      <Box>{listItems}</Box>
    </>
  )
}

export default SidebarItems
