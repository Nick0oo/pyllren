import { useEffect } from "react"
import { Button, HStack, Input, VStack } from "@chakra-ui/react"
import { FormProvider, useForm } from "react-hook-form"
import { Field } from "../ui/field"
import ProductosTable from "./ProductosTable"
import { useRecepciones, type RecepcionLotePayload } from "@/hooks/useRecepciones"
import { useQuery } from "@tanstack/react-query"
import { OpenAPI } from "@/client"
import { request as apiRequest } from "@/client/core/request"
import useCustomToast from "@/hooks/useCustomToast"

type Props = {
  alcance: {
    isAdmin: boolean
    scopeSucursalId: number | null
    setAdminSucursalId: (id: number | null) => void
    sucursales: Array<{ id_sucursal: number; nombre: string }>
    bodegas: Array<{ id_bodega: number; id_sucursal: number; nombre: string }>
  }
}

type FormValues = RecepcionLotePayload & { id_sucursal?: number | null }

const RecepcionForm = ({ alcance }: Props) => {
  const methods = useForm<FormValues>({
    defaultValues: {
      id_sucursal: alcance.scopeSucursalId ?? undefined,
      lote: {
        fecha_fabricacion: "",
        fecha_vencimiento: "",
        estado: "Activo",
        observaciones: "",
        id_proveedor: 0,
        id_bodega: 0,
      },
      items: [],
    },
    mode: "onBlur",
  })

  // Actualizar id_sucursal cuando cambie el alcance
  useEffect(() => {
    if (alcance.scopeSucursalId !== null) {
      methods.setValue("id_sucursal", alcance.scopeSucursalId)
    }
  }, [alcance.scopeSucursalId, methods])

  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { recepcionMutation } = useRecepciones()

  const proveedoresQuery = useQuery<{ data: Array<{ id_proveedor: number; nombre: string }>; count: number }>({
    queryKey: ["proveedores"],
    queryFn: () => apiRequest(OpenAPI, { method: "GET", url: "/api/v1/proveedores/", query: { skip: 0, limit: 200 } }),
  })

  const onSubmit = (data: FormValues) => {
    // Validar que haya al menos un producto
    if (!data.items || data.items.length === 0) {
      showErrorToast("Debe agregar al menos un producto")
      return
    }

    // Validar fechas
    if (data.lote.fecha_fabricacion && data.lote.fecha_vencimiento) {
      if (new Date(data.lote.fecha_fabricacion) > new Date(data.lote.fecha_vencimiento)) {
        showErrorToast("La fecha de fabricación no puede ser mayor a la de vencimiento")
        return
      }
    }

    // Preparar payload sin id_sucursal (solo para UI)
    // Convertir -1 (Sin bodega) a null si es necesario
    const loteData = {
      ...data.lote,
      id_bodega: data.lote.id_bodega === -1 ? null : (data.lote.id_bodega > 0 ? data.lote.id_bodega : null),
    }
    
    // Remover numero_lote del payload, se genera automáticamente
    const { numero_lote, ...loteDataSinNumero } = loteData as any
    
    const payload: RecepcionLotePayload = {
      lote: loteDataSinNumero,
      items: data.items.map((item) => ({
        ...item,
        nombre_generico: (item.nombre_generico && item.nombre_generico.trim() !== "") ? item.nombre_generico : null,
        codigo_interno: (item.codigo_interno && item.codigo_interno.trim() !== "") ? item.codigo_interno : null,
        codigo_barras: (item.codigo_barras && item.codigo_barras.trim() !== "") ? item.codigo_barras : null,
      })),
    }

    recepcionMutation.mutate(payload, {
      onSuccess: () => {
        methods.reset()
      },
      onError: (error: any) => {
        // Manejo mejorado de errores 422
        if (error?.body?.detail) {
          const detail = error.body.detail
          if (Array.isArray(detail)) {
            const messages = detail.map((d: any) => `${d.loc?.join(".")}: ${d.msg}`).join(", ")
            showErrorToast(`Error de validación: ${messages}`)
          } else if (typeof detail === "string") {
            showErrorToast(`Error: ${detail}`)
          }
        } else {
          handleError(error)
        }
      },
    })
  }

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <VStack gap={4} align="stretch" p={4} borderWidth="1px" borderRadius="md">
          {/* Mostrar sucursal para todos, pero solo admins pueden cambiarla */}
          {alcance.sucursales.length > 0 && (
            <Field label="Sucursal">
              <select
                style={{ 
                  width: "100%", 
                  height: "40px", 
                  padding: "8px 12px", 
                  fontSize: "14px", 
                  border: "1px solid #e2e8f0", 
                  borderRadius: "6px",
                  backgroundColor: alcance.isAdmin ? undefined : "#f7fafc",
                  cursor: alcance.isAdmin ? "pointer" : "not-allowed"
                }}
                value={alcance.scopeSucursalId ?? ""}
                disabled={!alcance.isAdmin}
                onChange={(e) => {
                  const id = e.target.value ? Number(e.target.value) : null
                  alcance.setAdminSucursalId(id)
                  methods.setValue("id_sucursal", id)
                }}
              >
                {alcance.isAdmin && <option value="">Todas</option>}
                {alcance.sucursales.map((s) => (
                  <option key={s.id_sucursal} value={s.id_sucursal}>
                    {s.nombre}
                  </option>
                ))}
              </select>
            </Field>
          )}

          <HStack gap={4}>
            <Field label="Proveedor" required invalid={!!methods.formState.errors?.lote?.id_proveedor}>
              <select
                style={{ width: "100%", height: "40px", padding: "8px 12px", fontSize: "14px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                {...methods.register("lote.id_proveedor", { valueAsNumber: true, min: 1 })}
              >
                <option value={0}>Seleccionar proveedor</option>
                {(proveedoresQuery.data?.data || []).map((p) => (
                  <option key={p.id_proveedor} value={p.id_proveedor}>
                    {p.nombre}
                  </option>
                ))}
              </select>
            </Field>
          </HStack>

          <HStack gap={4}>
            <Field label="Fecha de fabricación" required>
              <Input type="date" {...methods.register("lote.fecha_fabricacion", { required: true })} />
            </Field>
            <Field label="Fecha de vencimiento" required>
              <Input type="date" {...methods.register("lote.fecha_vencimiento", { required: true })} />
            </Field>
          </HStack>

          <HStack gap={4}>
            <Field label="Bodega de destino">
              <select
                style={{ width: "100%", height: "40px", padding: "8px 12px", fontSize: "14px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                {...methods.register("lote.id_bodega", { 
                  valueAsNumber: true,
                })}
              >
                <option value={0}>Seleccionar bodega</option>
                <option value={-1}>Sin bodega</option>
                {alcance.bodegas.map((b) => (
                  <option key={b.id_bodega} value={b.id_bodega}>
                    {b.nombre}
                  </option>
                ))}
              </select>
            </Field>
          </HStack>

          <Field label="Observaciones">
            <textarea
              rows={3}
              style={{ width: "100%", padding: "8px 12px", fontSize: "14px", border: "1px solid #e2e8f0", borderRadius: "6px", resize: "vertical" }}
              {...methods.register("lote.observaciones")}
            />
          </Field>

          <ProductosTable />

          <HStack gap={3} justify="flex-start">
            <Button type="submit" variant="solid" loading={methods.formState.isSubmitting}>
              Registrar Lote
            </Button>
            <Button
              variant="subtle"
              onClick={() => methods.reset()}
            >
              Limpiar
            </Button>
          </HStack>
        </VStack>
      </form>
    </FormProvider>
  )
}

export default RecepcionForm


