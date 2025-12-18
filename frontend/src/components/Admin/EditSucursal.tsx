import {
  Button,
  DialogActionTrigger,
  DialogRoot,
  DialogTrigger,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"

import { ApiError, OpenAPI, type SucursalPublic } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog"
import { Field } from "../ui/field"
import { Checkbox } from "../ui/checkbox"

export interface SucursalEditable extends SucursalPublic {
  nombre?: string
}

type SucursalUpdatePayload = {
  nombre?: string
  direccion?: string
  telefono?: string
  ciudad?: string
  estado?: boolean
}

const EditSucursal = ({ sucursal }: { sucursal: SucursalEditable }) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const defaultNombre = (sucursal as any).nombre ?? sucursal.nombre_sucursal

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SucursalUpdatePayload>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      nombre: defaultNombre,
      direccion: sucursal.direccion as any,
      telefono: sucursal.telefono as any,
      ciudad: (sucursal as any).ciudad,
      estado: sucursal.estado,
    },
  })

  const putSucursal = async (payload: SucursalUpdatePayload) => {
    const tokenFn = OpenAPI.TOKEN
    const token = tokenFn ? (typeof tokenFn === 'function' ? await tokenFn({} as any) : tokenFn) : ""
    const res = await fetch(`${OpenAPI.BASE}/api/v1/sucursales/${sucursal.id_sucursal}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      let body: unknown = undefined
      try { body = await res.json() } catch {}
      const request = { method: "PUT", url: `/api/v1/sucursales/${sucursal.id_sucursal}`, body: payload }
      const response = { url: res.url, status: res.status, statusText: res.statusText, body }
      throw new ApiError(request as any, response as any, res.statusText)
    }
    return res.json()
  }

  const mutation = useMutation({
    mutationFn: putSucursal,
    onSuccess: () => {
      showSuccessToast("Sucursal actualizada exitosamente.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["sucursales"] })
    },
  })

  const onSubmit: SubmitHandler<SucursalUpdatePayload> = (data) => {
    mutation.mutate(data)
  }

  return (
    <DialogRoot size={{ base: "xs", md: "md" }} placement="center" open={isOpen} onOpenChange={({ open }) => setIsOpen(open)}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <FaExchangeAlt fontSize="16px" />
          Editar sucursal
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar sucursal</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Actualiza los detalles de la sucursal.</Text>
            <VStack gap={4}>
              <Field invalid={!!errors.nombre} errorText={errors.nombre?.message} label="Nombre">
                <Input {...register("nombre")} placeholder="Nombre" type="text" />
              </Field>
              <Field invalid={!!errors.direccion} errorText={errors.direccion?.message} label="Dirección">
                <Input {...register("direccion")} placeholder="Dirección" type="text" />
              </Field>
              <Field invalid={!!errors.telefono} errorText={errors.telefono?.message} label="Teléfono">
                <Input {...register("telefono")} placeholder="Teléfono" type="text" />
              </Field>
              <Field invalid={!!errors.ciudad} errorText={errors.ciudad?.message} label="Ciudad">
                <Input {...register("ciudad")} placeholder="Ciudad" type="text" />
              </Field>
              <Field colorPalette="teal">
                <Checkbox {...register("estado")}>¿Activa?</Checkbox>
              </Field>
            </VStack>
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray" disabled={isSubmitting}>Cancelar</Button>
            </DialogActionTrigger>
            <Button variant="solid" type="submit" loading={isSubmitting}>Guardar</Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </form>
      </DialogContent>
    </DialogRoot>
  )
}

export default EditSucursal


