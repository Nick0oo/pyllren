import {
  Button,
  DialogActionTrigger,
  DialogRoot,
  DialogTrigger,
  Input,
  Text,
  VStack,
  HStack,
  Textarea,
  IconButton,
} from "@chakra-ui/react"
import { Checkbox } from "@/components/ui/checkbox"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiEdit } from "react-icons/fi"
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
import { useBodegas, type BodegaPublicExtended, type BodegaPublic, type BodegaUpdate } from "@/hooks/useBodegas"
import { useAlcance } from "@/hooks/useAlcance"

const TIPOS_BODEGA = ["Principal", "Secundaria", "De tránsito"]

interface EditBodegaProps {
  bodega: BodegaPublicExtended | BodegaPublic
}

const EditBodega = ({ bodega }: EditBodegaProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const { showErrorToast } = useCustomToast()
  const { updateMutation } = useBodegas()
  const alcance = useAlcance()

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<BodegaUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      nombre: bodega.nombre,
      descripcion: bodega.descripcion || null,
      tipo: bodega.tipo,
      estado: bodega.estado,
      capacidad: bodega.capacidad,
      ubicacion: bodega.ubicacion || null,
      temperatura_min: bodega.temperatura_min || null,
      temperatura_max: bodega.temperatura_max || null,
      humedad_min: bodega.humedad_min || null,
      humedad_max: bodega.humedad_max || null,
      id_sucursal: bodega.id_sucursal,
    },
  })

  const temperaturaMin = watch("temperatura_min")
  const temperaturaMax = watch("temperatura_max")
  const humedadMin = watch("humedad_min")
  const humedadMax = watch("humedad_max")

  const onSubmit: SubmitHandler<BodegaUpdate> = (data) => {
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

    updateMutation.mutate(
      { id: bodega.id_bodega, data },
      {
        onSuccess: () => {
          reset()
          setIsOpen(false)
        },
        onError: handleError,
      }
    )
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "lg" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <IconButton variant="ghost" size="sm" aria-label="Editar bodega">
          <FiEdit />
        </IconButton>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar bodega</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Modifica los datos de la bodega.</Text>
            <VStack gap={4}>
              <Field invalid={!!errors.nombre} errorText={errors.nombre?.message} label="Nombre">
                <Input {...register("nombre")} placeholder="Nombre de la bodega" type="text" />
              </Field>

              <Field label="Descripción">
                <Textarea {...register("descripcion")} placeholder="Descripción" rows={3} />
              </Field>

              <Field invalid={!!errors.tipo} errorText={errors.tipo?.message} label="Tipo">
                <select
                  style={{
                    width: "100%",
                    height: "40px",
                    padding: "8px 12px",
                    fontSize: "14px",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                  }}
                  {...register("tipo")}
                >
                  {TIPOS_BODEGA.map((tipo) => (
                    <option key={tipo} value={tipo}>
                      {tipo}
                    </option>
                  ))}
                </select>
              </Field>

              <Field
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
                  {...register("id_sucursal", { valueAsNumber: true })}
                >
                  {alcance.sucursales.map((sucursal) => (
                    <option key={sucursal.id_sucursal} value={sucursal.id_sucursal}>
                      {sucursal.nombre}
                    </option>
                  ))}
                </select>
              </Field>

              <Field
                invalid={!!errors.capacidad}
                errorText={errors.capacidad?.message}
                label="Capacidad"
              >
                <Input
                  {...register("capacidad", {
                    valueAsNumber: true,
                    min: { value: 1, message: "La capacidad debe ser mayor a 0" },
                  })}
                  placeholder="Capacidad máxima"
                  type="number"
                  min={1}
                />
              </Field>

              <Field label="Ubicación">
                <Input {...register("ubicacion")} placeholder="Ej: Planta Baja - Sector A" type="text" />
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

              <Field>
                <Checkbox {...register("estado")} defaultChecked={bodega.estado}>
                  Bodega operativa
                </Checkbox>
              </Field>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray" disabled={isSubmitting}>
                Cancelar
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              type="submit"
              disabled={updateMutation.isPending}
              loading={isSubmitting || updateMutation.isPending}
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

export default EditBodega

