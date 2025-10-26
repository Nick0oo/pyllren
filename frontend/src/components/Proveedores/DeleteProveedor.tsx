import { Button, DialogTitle, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiTrash2 } from "react-icons/fi"

import { ProveedoresService } from "@/client"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTrigger,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"

interface DeleteProveedorProps {
  proveedor: { id_proveedor: number; nombre: string }
}

const DeleteProveedor = ({ proveedor }: DeleteProveedorProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteProveedor = async (id: number) => {
    await ProveedoresService.deleteProveedor({ id })
  }

  const mutation = useMutation({
    mutationFn: deleteProveedor,
    onSuccess: () => {
      showSuccessToast("El proveedor fue eliminado exitosamente")
      setIsOpen(false)
    },
    onError: () => {
      showErrorToast("Ocurrió un error al eliminar el proveedor")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["proveedores"] })
    },
  })

  const onSubmit = async () => {
    mutation.mutate(proveedor.id_proveedor)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      role="alertdialog"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" colorPalette="red">
          <FiTrash2 fontSize="16px" />
          Eliminar proveedor
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Eliminar proveedor</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              ¿Estás seguro de que deseas eliminar el proveedor{" "}
              <strong>{proveedor.nombre}</strong>? Los lotes asociados a este 
              proveedor <strong>no se eliminarán</strong>, pero el proveedor 
              será marcado como inactivo.
            </Text>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="red"
              type="submit"
              loading={isSubmitting}
            >
              Eliminar
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </form>
      </DialogContent>
    </DialogRoot>
  )
}

export default DeleteProveedor
