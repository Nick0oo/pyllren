import {
  Button,
  DialogActionTrigger,
  DialogRoot,
  DialogTrigger,
  Flex,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"

import { type ProveedorPublic, ProveedoresService, type ProveedorUpdate } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { emailPattern, handleError } from "@/utils"
import { Checkbox } from "../ui/checkbox"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog"
import { Field } from "../ui/field"

interface EditProveedorProps {
  proveedor: ProveedorPublic
}

const EditProveedor = ({ proveedor }: EditProveedorProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProveedorUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      nombre: proveedor.nombre,
      nit: proveedor.nit,
      telefono: proveedor.telefono,
      email: proveedor.email,
      direccion: proveedor.direccion,
      ciudad: proveedor.ciudad,
      estado: proveedor.estado,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: ProveedorUpdate) =>
      ProveedoresService.updateProveedor({ 
        id: proveedor.id_proveedor, 
        requestBody: data 
      }),
    onSuccess: () => {
      showSuccessToast("Proveedor actualizado exitosamente.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["proveedores"] })
    },
  })

  const onSubmit: SubmitHandler<ProveedorUpdate> = (data) => {
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
        <Button variant="ghost" size="sm">
          <FaExchangeAlt fontSize="16px" />
          Editar proveedor
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar proveedor</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Actualiza los detalles del proveedor a continuación.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.nombre}
                errorText={errors.nombre?.message}
                label="Nombre"
              >
                <Input
                  {...register("nombre", {
                    required: "El nombre es obligatorio",
                    maxLength: {
                      value: 255,
                      message: "El nombre no puede exceder 255 caracteres",
                    },
                  })}
                  placeholder="Nombre del proveedor"
                  type="text"
                />
              </Field>

              <Field
                required
                invalid={!!errors.nit}
                errorText={errors.nit?.message}
                label="NIT"
              >
                <Input
                  {...register("nit", {
                    required: "El NIT es obligatorio",
                    maxLength: {
                      value: 50,
                      message: "El NIT no puede exceder 50 caracteres",
                    },
                  })}
                  placeholder="NIT del proveedor"
                  type="text"
                />
              </Field>

              <Field
                required
                invalid={!!errors.telefono}
                errorText={errors.telefono?.message}
                label="Teléfono"
              >
                <Input
                  {...register("telefono", {
                    required: "El teléfono es obligatorio",
                    maxLength: {
                      value: 20,
                      message: "El teléfono no puede exceder 20 caracteres",
                    },
                  })}
                  placeholder="Teléfono"
                  type="tel"
                />
              </Field>

              <Field
                required
                invalid={!!errors.email}
                errorText={errors.email?.message}
                label="Email"
              >
                <Input
                  {...register("email", {
                    required: "El email es obligatorio",
                    pattern: emailPattern,
                  })}
                  placeholder="Email del proveedor"
                  type="email"
                />
              </Field>

              <Field
                required
                invalid={!!errors.direccion}
                errorText={errors.direccion?.message}
                label="Dirección"
              >
                <Input
                  {...register("direccion", {
                    required: "La dirección es obligatoria",
                    maxLength: {
                      value: 255,
                      message: "La dirección no puede exceder 255 caracteres",
                    },
                  })}
                  placeholder="Dirección completa"
                  type="text"
                />
              </Field>

              <Field
                required
                invalid={!!errors.ciudad}
                errorText={errors.ciudad?.message}
                label="Ciudad"
              >
                <Input
                  {...register("ciudad", {
                    required: "La ciudad es obligatoria",
                    maxLength: {
                      value: 100,
                      message: "La ciudad no puede exceder 100 caracteres",
                    },
                  })}
                  placeholder="Ciudad"
                  type="text"
                />
              </Field>
            </VStack>

            <Flex mt={4} direction="column" gap={4}>
              <Field colorPalette="teal">
                <Checkbox
                  {...register("estado")}
                  defaultChecked={proveedor.estado}
                >
                  ¿Está activo?
                </Checkbox>
              </Field>
            </Flex>
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
            <Button variant="solid" type="submit" loading={isSubmitting}>
              Guardar
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </form>
      </DialogContent>
    </DialogRoot>
  )
}

export default EditProveedor
