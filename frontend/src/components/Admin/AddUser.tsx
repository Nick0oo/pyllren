import {
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  Text,
  VStack,
  Grid,
  GridItem,
  HStack,
  IconButton,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"
import { type UserCreateByAdmin, UsersService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { useRolesAndSucursales } from "@/hooks/useRolesAndSucursales"
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
import { Select, SelectItem } from "../ui/select"

interface UserCreateByAdminForm extends Omit<UserCreateByAdmin, 'id_sucursal'> {
  confirm_password: string
  id_sucursal?: number | null
}

const AddUser = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const { roles, sucursales, isLoading, rolesError, sucursalesError, refetchRoles, refetchSucursales } = useRolesAndSucursales()
  
  const {
    control,
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isValid, isSubmitting },
  } = useForm<UserCreateByAdminForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
      id_rol: undefined,
      id_sucursal: null,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: UserCreateByAdmin) =>
      UsersService.createUserByAdmin({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Usuario creado exitosamente.")
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

  const onSubmit: SubmitHandler<UserCreateByAdminForm> = (data) => {
    // Preparar datos para el endpoint
    const { confirm_password, ...userData } = data
    mutation.mutate(userData)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button value="add-user" my={4}>
          <FaPlus fontSize="16px" />
          Agregar usuario
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Agregar usuario</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Completa el formulario para agregar un nuevo usuario al sistema.
            </Text>

            {(rolesError || sucursalesError) && (
              <HStack mb={3} gap={3} wrap="wrap">
                <Text color="red.300">
                  Hubo un problema cargando {rolesError && sucursalesError ? "roles y sucursales" : rolesError ? "los roles" : "las sucursales"}.
                </Text>
                <Button size="sm" variant="outline" onClick={() => { rolesError && refetchRoles(); sucursalesError && refetchSucursales(); }}>
                  Reintentar
                </Button>
              </HStack>
            )}

            <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={4}>
              <GridItem>
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
              </GridItem>

              <GridItem>
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
              </GridItem>

              <GridItem>
                <Field
                required
                invalid={!!errors.password}
                errorText={errors.password?.message}
                label="Establecer contraseña"
              >
                <Input
                  {...register("password", {
                    required: "La contraseña es obligatoria",
                    minLength: {
                      value: 8,
                      message: "La contraseña debe tener al menos 8 caracteres",
                    },
                  })}
                  placeholder="Contraseña"
                  type="password"
                />
                </Field>
              </GridItem>

              <GridItem>
                <Field
                required
                invalid={!!errors.confirm_password}
                errorText={errors.confirm_password?.message}
                label="Confirmar contraseña"
              >
                <Input
                  {...register("confirm_password", {
                    required: "Por favor confirma tu contraseña",
                    validate: (value) =>
                      value === getValues().password ||
                      "Las contraseñas no coinciden",
                  })}
                  placeholder="Contraseña"
                  type="password"
                />
                </Field>
              </GridItem>

              <Field
                required
                invalid={!!errors.id_rol}
                errorText={errors.id_rol?.message}
                label="Rol"
              >
                 <Controller
                   control={control}
                   name="id_rol"
                   rules={{ required: "El rol es obligatorio" }}
                   render={({ field }) => (
                     <Select
                       placeholder="Seleccionar rol"
                       value={field.value?.toString() || ""}
                       onChange={(e) => field.onChange(parseInt(e.target.value))}
                       disabled={isLoading}
                     >
                       {roles.map((rol: any) => (
                         <SelectItem key={rol.id_rol} value={rol.id_rol}>
                           {rol.nombre_rol}
                         </SelectItem>
                       ))}
                     </Select>
                   )}
                 />
              </Field>

              <Field
                invalid={!!errors.id_sucursal}
                errorText={errors.id_sucursal?.message}
                label="Sucursal (opcional)"
              >
                <Controller
                  control={control}
                  name="id_sucursal"
                  render={({ field }) => (
                    <Select
                      placeholder="Seleccionar sucursal (opcional)"
                      value={field.value !== null && field.value !== undefined ? String(field.value) : ""}
                      onChange={(e) =>
                        field.onChange(e.target.value ? parseInt(e.target.value) : null)
                      }
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
            </Grid>

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

export default AddUser
