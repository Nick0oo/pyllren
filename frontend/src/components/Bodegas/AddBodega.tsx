import {
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  Text,
  VStack,
  HStack,
  Textarea,
} from "@chakra-ui/react"
import { useState } from "react"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
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
import { Checkbox } from "../ui/checkbox"
import { useBodegas, type BodegaCreate } from "@/hooks/useBodegas"
import { usePermissions } from "@/hooks/usePermissions"
import { useAlcance } from "@/hooks/useAlcance"

const TIPOS_BODEGA = ["Principal", "Secundaria", "De tránsito"]

const AddBodega = () => {
  const [isOpen, setIsOpen] = useState(false)
  const { showErrorToast } = useCustomToast()
  const { createMutation } = useBodegas()
  const { isAdmin } = usePermissions()
  const alcance = useAlcance()

  // Solo admin puede crear bodegas
  if (!isAdmin()) {
    return null
  }

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isValid, isSubmitting },
  } = useForm<BodegaCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      nombre: "",
      descripcion: null,
      tipo: "Principal",
      estado: true,
      capacidad: 0,
      ubicacion: null,
      temperatura_min: null,
      temperatura_max: null,
      humedad_min: null,
      humedad_max: null,
      id_sucursal: alcance.sucursales[0]?.id_sucursal || 0,
    },
  })

  const temperaturaMin = watch("temperatura_min")
  const temperaturaMax = watch("temperatura_max")
  const humedadMin = watch("humedad_min")
  const humedadMax = watch("humedad_max")

  const onSubmit: SubmitHandler<BodegaCreate> = (data) => {
    // Validaciones adicionales
    if (
      temperaturaMin !== null &&
      temperaturaMin !== undefined &&
      temperaturaMax !== null &&
      temperaturaMax !== undefined &&
      temperaturaMin >= temperaturaMax
    ) {
      showErrorToast("La temperatura mínima debe ser menor que la máxima")
      return
    }

    if (
      humedadMin !== null &&
      humedadMin !== undefined &&
      humedadMax !== null &&
      humedadMax !== undefined &&
      humedadMin >= humedadMax
    ) {
      showErrorToast("La humedad mínima debe ser menor que la máxima")
      return
    }

    if (humedadMin !== null && humedadMin !== undefined && (humedadMin < 0 || humedadMin > 100)) {
      showErrorToast("La humedad mínima debe estar entre 0 y 100")
      return
    }

    if (humedadMax !== null && humedadMax !== undefined && (humedadMax < 0 || humedadMax > 100)) {
      showErrorToast("La humedad máxima debe estar entre 0 y 100")
      return
    }

    createMutation.mutate(data, {
      onSuccess: () => {
        reset()
        setIsOpen(false)
      },
      onError: handleError,
    })
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "lg" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button value="add-bodega" my={4}>
          <FaPlus fontSize="16px" />
          Nueva Bodega
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Agregar bodega</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Completa el formulario para agregar una nueva bodega al sistema.
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
                  })}
                  placeholder="Nombre de la bodega"
                  type="text"
                />
              </Field>

              <Field label="Descripción">
                <Textarea
                  {...register("descripcion")}
                  placeholder="Descripción de la bodega"
                  rows={3}
                />
              </Field>

              <Field
                required
                invalid={!!errors.tipo}
                errorText={errors.tipo?.message}
                label="Tipo"
              >
                <select
                  style={{
                    width: "100%",
                    height: "40px",
                    padding: "8px 12px",
                    fontSize: "14px",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                  }}
                  {...register("tipo", { required: true })}
                >
                  {TIPOS_BODEGA.map((tipo) => (
                    <option key={tipo} value={tipo}>
                      {tipo}
                    </option>
                  ))}
                </select>
              </Field>

              <Field
                required
                invalid={!!errors.id_sucursal}
                errorText={errors.id_sucursal?.message}
                label="Sucursal"
              >
                <select
                  style={{
                    width: "100%",
                    height: "40px",
                    padding: "8px 12px",
                    fontSize: "14px",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                  }}
                  {...register("id_sucursal", {
                    required: "La sucursal es obligatoria",
                    valueAsNumber: true,
                  })}
                >
                  <option value={0}>Seleccionar sucursal</option>
                  {alcance.sucursales.map((sucursal) => (
                    <option key={sucursal.id_sucursal} value={sucursal.id_sucursal}>
                      {sucursal.nombre}
                    </option>
                  ))}
                </select>
              </Field>

              <Field
                required
                invalid={!!errors.capacidad}
                errorText={errors.capacidad?.message}
                label="Capacidad"
              >
                <Input
                  {...register("capacidad", {
                    required: "La capacidad es obligatoria",
                    valueAsNumber: true,
                    min: { value: 1, message: "La capacidad debe ser mayor a 0" },
                  })}
                  placeholder="Capacidad máxima"
                  type="number"
                  min={1}
                />
              </Field>

              <Field label="Ubicación">
                <Input
                  {...register("ubicacion")}
                  placeholder="Ej: Planta Baja - Sector A"
                  type="text"
                />
              </Field>

              <HStack gap={2} width="100%">
                <Field label="Temp. Mín (°C)">
                  <Input
                    {...register("temperatura_min", { valueAsNumber: true })}
                    placeholder="Mín"
                    type="number"
                    step="0.1"
                  />
                </Field>
                <Field label="Temp. Máx (°C)">
                  <Input
                    {...register("temperatura_max", { valueAsNumber: true })}
                    placeholder="Máx"
                    type="number"
                    step="0.1"
                  />
                </Field>
              </HStack>

              <HStack gap={2} width="100%">
                <Field label="Humedad Mín (%)">
                  <Input
                    {...register("humedad_min", {
                      valueAsNumber: true,
                      min: { value: 0, message: "Debe ser >= 0" },
                      max: { value: 100, message: "Debe ser <= 100" },
                    })}
                    placeholder="Mín"
                    type="number"
                    min={0}
                    max={100}
                  />
                </Field>
                <Field label="Humedad Máx (%)">
                  <Input
                    {...register("humedad_max", {
                      valueAsNumber: true,
                      min: { value: 0, message: "Debe ser >= 0" },
                      max: { value: 100, message: "Debe ser <= 100" },
                    })}
                    placeholder="Máx"
                    type="number"
                    min={0}
                    max={100}
                  />
                </Field>
              </HStack>

              <Controller
                control={control}
                name="estado"
                render={({ field }) => (
                  <Field>
                    <Checkbox
                      checked={!!field.value}
                      onCheckedChange={({ checked }) => field.onChange(checked)}
                    >
                      Bodega operativa
                    </Checkbox>
                  </Field>
                )}
              />
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
              disabled={!isValid || createMutation.isPending}
              loading={isSubmitting || createMutation.isPending}
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

export default AddBodega

