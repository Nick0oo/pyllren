import { IconButton } from "@chakra-ui/react"
import { BsThreeDotsVertical } from "react-icons/bs"

import { type ProveedorPublic } from "@/client"
import DeleteProveedor from "@/components/Proveedores/DeleteProveedor"
import EditProveedor from "@/components/Proveedores/EditProveedor"
import { MenuContent, MenuRoot, MenuTrigger } from "@/components/ui/menu"

interface ProveedorActionsMenuProps {
  proveedor: ProveedorPublic
  disabled?: boolean
}

export const ProveedorActionsMenu = ({ proveedor, disabled }: ProveedorActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton variant="ghost" color="inherit" disabled={disabled}>
          <BsThreeDotsVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditProveedor proveedor={proveedor} />
        <DeleteProveedor proveedor={proveedor} />
      </MenuContent>
    </MenuRoot>
  )
}
