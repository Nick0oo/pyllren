import {
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"

import { ProveedoresService, type ProveedorCreate } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { emailPattern, handleError } from "@/utils"
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

const AddProveedor = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<ProveedorCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      nombre: "",
      nit: "",
      telefono: "",
      email: "",
      direccion: "",
      ciudad: "",
      estado: true,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: ProveedorCreate) =>
      ProveedoresService.createProveedor({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Proveedor creado exitosamente.")
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

  const onSubmit: SubmitHandler<ProveedorCreate> = (data) => {
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
        <Button value="add-proveedor" my={4}>
          <FaPlus fontSize="16px" />
          Nuevo proveedor
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Agregar proveedor</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Completa el formulario para agregar un nuevo proveedor al sistema.
            </Text>
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
              type="submit"
              disabled={!isValid}
              loading={isSubmitting}
            >
              Guardar
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddProveedor
