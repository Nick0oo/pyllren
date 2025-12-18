import {
  Button,
  DialogTitle,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"

import { ApiError, OpenAPI, type SucursalPublic } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { Checkbox } from "../ui/checkbox"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTrigger,
} from "../ui/dialog"
import { Field } from "../ui/field"

type SucursalCreatePayload = {
  nombre: string
  direccion: string
  telefono: string
  ciudad: string
  estado?: boolean
}

const AddSucursal = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<SucursalCreatePayload>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      nombre: "",
      direccion: "",
      telefono: "",
      ciudad: "",
      estado: true,
    },
  })

  const postSucursal = async (payload: SucursalCreatePayload): Promise<SucursalPublic> => {
    const tokenFn = OpenAPI.TOKEN
    const token = tokenFn ? (typeof tokenFn === 'function' ? await tokenFn({} as any) : tokenFn) : ""
    const res = await fetch(`${OpenAPI.BASE}/api/v1/sucursales/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      let body: unknown = undefined
      try {
        body = await res.json()
      } catch {
        body = undefined
      }
      const request = { method: "POST", url: "/api/v1/sucursales/", body: payload }
      const response = { url: res.url, status: res.status, statusText: res.statusText, body }
      throw new ApiError(request as any, response as any, res.statusText)
    }
    return res.json()
  }

  const mutation = useMutation({
    mutationFn: postSucursal,
    onSuccess: () => {
      showSuccessToast("Sucursal creada exitosamente.")
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

  const onSubmit: SubmitHandler<SucursalCreatePayload> = (data) => {
    mutation.mutate(data)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button value="add-sucursal" my={4}>
          <FaPlus fontSize="16px" />
          Agregar sucursal
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Agregar sucursal</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Completa el formulario para crear una nueva sucursal.</Text>
            <VStack gap={4}>
              <Field required invalid={!!errors.nombre} errorText={errors.nombre?.message} label="Nombre">
                <Input
                  {...register("nombre", { required: "El nombre es obligatorio" })}
                  placeholder="Nombre de la sucursal"
                  type="text"
                />
              </Field>

              <Field required invalid={!!errors.direccion} errorText={errors.direccion?.message} label="Dirección">
                <Input
                  {...register("direccion", { required: "La dirección es obligatoria" })}
                  placeholder="Dirección"
                  type="text"
                />
              </Field>

              <Field required invalid={!!errors.telefono} errorText={errors.telefono?.message} label="Teléfono">
                <Input
                  {...register("telefono", {
                    required: "El teléfono es obligatorio",
                    pattern: {
                      value: /^[0-9+\-()\s]{6,20}$/,
                      message: "Teléfono inválido",
                    },
                  })}
                  placeholder="Teléfono"
                  type="text"
                />
              </Field>

              <Field required invalid={!!errors.ciudad} errorText={errors.ciudad?.message} label="Ciudad">
                <Input
                  {...register("ciudad", { required: "La ciudad es obligatoria" })}
                  placeholder="Ciudad"
                  type="text"
                />
              </Field>

              <Controller
                control={control}
                name="estado"
                render={({ field }) => (
                  <Field disabled={field.disabled} colorPalette="teal">
                    <Checkbox
                      checked={!!field.value}
                      onCheckedChange={({ checked }) => field.onChange(checked)}
                    >
                      ¿Sucursal activa?
                    </Checkbox>
                  </Field>
                )}
              />
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <Button variant="subtle" colorPalette="gray" type="button" onClick={() => setIsOpen(false)} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button variant="solid" type="submit" disabled={!isValid} loading={isSubmitting}>
              Guardar
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddSucursal


