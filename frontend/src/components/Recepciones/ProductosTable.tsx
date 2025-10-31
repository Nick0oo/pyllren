import { Button, Grid, GridItem, HStack, Input, VStack } from "@chakra-ui/react"
import { useFieldArray, useFormContext } from "react-hook-form"
import { FaPlus, FaTrash } from "react-icons/fa"
import { Field } from "../ui/field"
import { useQuery } from "@tanstack/react-query"
import { OpenAPI } from "@/client"
import { request as apiRequest } from "@/client/core/request"
import { useState } from "react"

type FormValues = {
  items: Array<{
    nombre_comercial: string
    nombre_generico?: string | null
    codigo_interno?: string | null
    codigo_barras?: string | null
    forma_farmaceutica: string
    concentracion: string
    presentacion: string
    unidad_medida: string
    cantidad: number
    stock_minimo: number
    stock_maximo: number
  }>
}

const UNIDADES = ["unidad", "blister", "caja", "frasco", "ampolla", "bolsa", "sobre", "tubo"]
const PRESENTACIONES = ["Tableta", "Cápsula", "Jarabe", "Inyectable", "Crema", "Gotas", "Suspensión", "Polvo"]
const FORMAS = ["Tableta", "Cápsula", "Jarabe", "Inyectable", "Crema", "Gotas", "Suspensión", "Polvo", "Ungüento"]

const defaultRow = {
  nombre_comercial: "",
  nombre_generico: null,
  codigo_interno: null,
  codigo_barras: null,
  forma_farmaceutica: "",
  concentracion: "",
  presentacion: "",
  unidad_medida: "unidad",
  cantidad: 0,
  stock_minimo: 0,
  stock_maximo: 0,
}

const ProductosTable = () => {
  const { control, register, formState, setValue } = useFormContext<FormValues>()
  const { fields, append, remove } = useFieldArray({ control, name: "items" })
  const [showAdvanced, setShowAdvanced] = useState<Record<number, boolean>>({})

  // Cargar productos para búsqueda (opcional)
  const productosQuery = useQuery({
    queryKey: ["productos", "all"],
    queryFn: async () => {
      const response = await apiRequest(OpenAPI, {
        method: "GET",
        url: "/api/v1/productos/",
        query: { skip: 0, limit: 500 },
      })
      return (response as any)?.data || []
    },
  })

  const handleSearchProduct = (index: number, searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) return

    const productos = productosQuery.data || []
    const searchLower = searchTerm.toLowerCase()

    const productoEncontrado = productos.find(
      (p: any) =>
        p.codigo_interno?.toLowerCase().includes(searchLower) ||
        p.nombre_comercial?.toLowerCase().includes(searchLower) ||
        p.nombre_generico?.toLowerCase().includes(searchLower)
    )

    if (productoEncontrado) {
      setValue(`items.${index}.nombre_comercial`, productoEncontrado.nombre_comercial || "")
      setValue(`items.${index}.nombre_generico`, productoEncontrado.nombre_generico || null)
      setValue(`items.${index}.codigo_interno`, productoEncontrado.codigo_interno || null)
      setValue(`items.${index}.forma_farmaceutica`, productoEncontrado.forma_farmaceutica || "")
      setValue(`items.${index}.concentracion`, productoEncontrado.concentracion || "")
      setValue(`items.${index}.presentacion`, productoEncontrado.presentacion || "")
      setValue(`items.${index}.unidad_medida`, productoEncontrado.unidad_medida || "unidad")
      setValue(`items.${index}.stock_minimo`, productoEncontrado.stock_minimo || 0)
      setValue(`items.${index}.stock_maximo`, productoEncontrado.stock_maximo || 0)
    }
  }

  return (
    <VStack gap={4} align="stretch">
      {fields.map((field, index) => (
        <VStack key={field.id} gap={3} p={4} borderWidth="1px" borderRadius="md" bg="bg.surface">
          <Grid templateColumns="repeat(2, 1fr)" gap={3} w="full">
            <GridItem colSpan={2}>
              <Field label="Nombre comercial *" required invalid={!!formState.errors?.items?.[index]?.nombre_comercial}>
                <Input
                  {...register(`items.${index}.nombre_comercial` as const, { required: "Campo requerido" })}
                  placeholder="Ej: Paracetamol"
                />
              </Field>
            </GridItem>
            
            <GridItem>
              <Field label="Forma farmacéutica *" required>
                <select
                  style={{ width: "100%", height: "40px", padding: "8px 12px", fontSize: "14px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                  {...register(`items.${index}.forma_farmaceutica` as const, { required: true })}
                >
                  <option value="">Seleccionar...</option>
                  {FORMAS.map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </Field>
            </GridItem>
            
            <GridItem>
              <Field label="Concentración *" required>
                <Input
                  {...register(`items.${index}.concentracion` as const, { required: true })}
                  placeholder="Ej: 500 mg"
                />
              </Field>
            </GridItem>
            
            <GridItem>
              <Field label="Presentación *" required>
                <select
                  style={{ width: "100%", height: "40px", padding: "8px 12px", fontSize: "14px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                  {...register(`items.${index}.presentacion` as const, { required: true })}
                >
                  <option value="">Seleccionar...</option>
                  {PRESENTACIONES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </Field>
            </GridItem>
            
            <GridItem>
              <Field label="Unidad de medida *" required>
                <select
                  style={{ width: "100%", height: "40px", padding: "8px 12px", fontSize: "14px", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                  {...register(`items.${index}.unidad_medida` as const, { required: true })}
                >
                  {UNIDADES.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </Field>
            </GridItem>
            
            <GridItem>
              <Field label="Cantidad *" required invalid={!!formState.errors?.items?.[index]?.cantidad}>
                <Input
                  type="number"
                  {...register(`items.${index}.cantidad` as const, { valueAsNumber: true, min: 1, required: true })}
                  placeholder="0"
                />
              </Field>
            </GridItem>
            
            <GridItem>
              <Field label="Stock mínimo">
                <Input
                  type="number"
                  {...register(`items.${index}.stock_minimo` as const, { valueAsNumber: true, min: 0 })}
                  placeholder="0"
                />
              </Field>
            </GridItem>
            
            <GridItem>
              <Field label="Stock máximo">
                <Input
                  type="number"
                  {...register(`items.${index}.stock_maximo` as const, { valueAsNumber: true, min: 0 })}
                  placeholder="0"
                />
              </Field>
            </GridItem>
            
            <GridItem colSpan={2}>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced((prev) => ({ ...prev, [index]: !prev[index] }))}
              >
                {showAdvanced[index] ? "Ocultar" : "Mostrar"} campos opcionales
              </Button>
            </GridItem>
            
            {showAdvanced[index] && (
              <>
                <GridItem>
                  <Field label="Nombre genérico">
                    <Input
                      {...register(`items.${index}.nombre_generico` as const)}
                      placeholder="Ej: Acetaminofén"
                    />
                  </Field>
                </GridItem>
                <GridItem>
                  <Field label="Código interno">
                    <Input {...register(`items.${index}.codigo_interno` as const)} />
                  </Field>
                </GridItem>
              </>
            )}
          </Grid>
          
          <HStack w="full" justify="flex-end">
            <Button
              aria-label="remove-row"
              colorPalette="red"
              variant="outline"
              onClick={() => {
                remove(index)
                setShowAdvanced((prev) => {
                  const newState = { ...prev }
                  delete newState[index]
                  return newState
                })
              }}
            >
              <FaTrash />
              Eliminar
            </Button>
          </HStack>
        </VStack>
      ))}
      
      <Button onClick={() => append(defaultRow)} leftIcon={<FaPlus />} variant="outline">
        Añadir producto
      </Button>
    </VStack>
  )
}

export default ProductosTable
