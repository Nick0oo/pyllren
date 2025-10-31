import { Button, DialogTitle, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiTrash2 } from "react-icons/fi"

import { ApiError, OpenAPI } from "@/client"
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

interface DeleteSucursalProps {
  sucursal: { id_sucursal: number; nombre?: string; nombre_sucursal?: string }
}

const DeleteSucursal = ({ sucursal }: DeleteSucursalProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteSucursal = async (id: number) => {
    const token = (await OpenAPI.TOKEN?.()) || ""
    const res = await fetch(`${OpenAPI.BASE}/api/v1/sucursales/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    if (!res.ok) {
      let body: unknown = undefined
      try { body = await res.json() } catch {}
      throw new ApiError({ url: res.url, status: res.status, statusText: res.statusText, body })
    }
    return res.json()
  }

  const mutation = useMutation({
    mutationFn: () => deleteSucursal(sucursal.id_sucursal),
    onSuccess: () => {
      showSuccessToast("La sucursal fue eliminada exitosamente")
      setIsOpen(false)
    },
    onError: () => {
      showErrorToast("Ocurrió un error al eliminar la sucursal")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["sucursales"] })
    },
  })

  const onSubmit = async () => {
    mutation.mutate()
  }

  const nombre = (sucursal.nombre_sucursal || (sucursal as any).nombre || "la sucursal") as string

  return (
    <DialogRoot size={{ base: "xs", md: "md" }} placement="center" role="alertdialog" open={isOpen} onOpenChange={({ open }) => setIsOpen(open)}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" colorPalette="red">
          <FiTrash2 fontSize="16px" />
          Eliminar sucursal
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Eliminar sucursal</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              ¿Estás seguro de que deseas eliminar <strong>{nombre}</strong>? Esta acción no se puede deshacer.
            </Text>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray" disabled={isSubmitting}>Cancelar</Button>
            </DialogActionTrigger>
            <Button variant="solid" colorPalette="red" type="submit" loading={isSubmitting}>Eliminar</Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </form>
      </DialogContent>
    </DialogRoot>
  )
}

export default DeleteSucursal


