import { Button, DialogTitle, Text, IconButton } from "@chakra-ui/react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiTrash2 } from "react-icons/fi"
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
import { useBodegas, type BodegaPublicExtended } from "@/hooks/useBodegas"
import type { BodegaPublic } from "@/client"

interface DeleteBodegaProps {
  bodega: BodegaPublicExtended | BodegaPublic
}

const DeleteBodega = ({ bodega }: DeleteBodegaProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const { showErrorToast } = useCustomToast()
  const { deleteMutation } = useBodegas()
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const onSubmit = async () => {
    deleteMutation.mutate(bodega.id_bodega, {
      onSuccess: () => {
        setIsOpen(false)
      },
      onError: () => {
        showErrorToast("Ocurrió un error al eliminar la bodega")
      },
    })
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
        <IconButton
          variant="ghost"
          size="sm"
          colorPalette="red"
          aria-label="Eliminar bodega"
        >
          <FiTrash2 />
        </IconButton>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Eliminar bodega</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              ¿Estás seguro de que deseas eliminar la bodega{" "}
              <strong>{bodega.nombre}</strong>? La bodega será marcada como
              inactiva (soft delete). Los lotes y productos asociados{" "}
              <strong>no se eliminarán</strong>.
            </Text>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray" disabled={isSubmitting}>
                Cancelar
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="red"
              type="submit"
              loading={isSubmitting || deleteMutation.isPending}
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

export default DeleteBodega

