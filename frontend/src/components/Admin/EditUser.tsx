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
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"

import { type UserPublic, UsersService, type UserUpdate } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { emailPattern, handleError } from "@/utils"
import { useRolesAndSucursales } from "@/hooks/useRolesAndSucursales"
import { Select, SelectItem } from "../ui/select"
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

interface EditUserProps {
  user: UserPublic
}

interface UserUpdateForm extends UserUpdate {
  confirm_password?: string
  id_rol?: number | null
  id_sucursal?: number | null
}

const EditUser = ({ user }: EditUserProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const { roles, sucursales, isLoading } = useRolesAndSucursales()
  const {
    control,
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<UserUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: user,
  })

  const mutation = useMutation({
    mutationFn: (data: UserUpdateForm) =>
      UsersService.updateUser({ userId: user.id, requestBody: data as unknown as UserUpdate }),
    onSuccess: () => {
      showSuccessToast("User updated successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const onSubmit: SubmitHandler<UserUpdateForm> = async (data) => {
    if (data.password === "") {
      data.password = undefined
    }
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
          Editar usuario
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar usuario</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Actualiza los detalles del usuario a continuación.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.email}
                errorText={errors.email?.message}
                label="Correo"
              >
                <Input
                  {...register("email", {
                    required: "El correo es obligatorio",
                    pattern: emailPattern,
                  })}
                  placeholder="Correo"
                  type="email"
                />
              </Field>

              <Field
                invalid={!!errors.full_name}
                errorText={errors.full_name?.message}
                label="Nombre completo"
              >
                <Input
                  {...register("full_name")}
                  placeholder="Nombre completo"
                  type="text"
                />
              </Field>

              <Field
                invalid={!!errors.password}
                errorText={errors.password?.message}
                label="Establecer contraseña"
              >
                <Input
                  {...register("password", {
                    minLength: {
                      value: 8,
                      message: "Password must be at least 8 characters",
                    },
                  })}
                  placeholder="Password"
                  type="password"
                />
              </Field>

              <Field
                invalid={!!errors.confirm_password}
                errorText={errors.confirm_password?.message}
                label="Confirm Password"
              >
                <Input
                  {...register("confirm_password", {
                    validate: (value) =>
                      value === getValues().password ||
                      "The passwords do not match",
                  })}
                  placeholder="Password"
                  type="password"
                />
              </Field>

              <Field
                invalid={!!errors.id_rol}
                errorText={errors.id_rol as any}
                label="Rol"
              >
                <Controller
                  control={control}
                  name="id_rol"
                  render={({ field }) => (
                    <Select
                      placeholder="Seleccionar rol"
                      value={field.value != null ? String(field.value) : ""}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : null)}
                      disabled={isLoading}
                    >
                      <SelectItem value="">Sin rol</SelectItem>
                      {roles.map((rol: any) => (
                        <SelectItem key={rol.id_rol} value={String(rol.id_rol)}>
                          {rol.nombre_rol}
                        </SelectItem>
                      ))}
                    </Select>
                  )}
                />
              </Field>

              <Field
                invalid={!!errors.id_sucursal}
                errorText={errors.id_sucursal as any}
                label="Sucursal"
              >
                <Controller
                  control={control}
                  name="id_sucursal"
                  render={({ field }) => (
                    <Select
                      placeholder="Seleccionar sucursal"
                      value={field.value != null ? String(field.value) : ""}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : null)}
                      disabled={isLoading}
                    >
                      <SelectItem value="">Sin sucursal</SelectItem>
                      {sucursales.map((sucursal: any) => (
                        <SelectItem key={sucursal.id_sucursal} value={String(sucursal.id_sucursal)}>
                          {sucursal.nombre_sucursal}
                        </SelectItem>
                      ))}
                    </Select>
                  )}
                />
              </Field>
            </VStack>

            <Flex mt={4} direction="column" gap={4}>
              <Controller
                control={control}
                name="is_superuser"
                render={({ field }) => (
                  <Field disabled={field.disabled} colorPalette="teal">
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={({ checked }) => field.onChange(checked)}
                    >
                      ¿Es superusuario?
                    </Checkbox>
                  </Field>
                )}
              />
              <Controller
                control={control}
                name="is_active"
                render={({ field }) => (
                  <Field disabled={field.disabled} colorPalette="teal">
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={({ checked }) => field.onChange(checked)}
                    >
                      ¿Está activo?
                    </Checkbox>
                  </Field>
                )}
              />
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

export default EditUser
