# Sistema de Validación de Capacidad de Bodegas

## 🎯 Descripción

Sistema completo de validación de capacidad de bodegas implementado en el módulo de recepciones. Previene la sobresaturación de bodegas y sugiere distribución automática cuando se excede la capacidad.

## 🏗️ Arquitectura

### Backend (Python/FastAPI)

#### Funciones Auxiliares
- **`calcular_ocupacion_bodega()`**: Calcula ocupación actual con lock pesimista (SELECT FOR UPDATE)
- **`obtener_bodegas_alternativas()`**: Busca bodegas disponibles en la misma sucursal
- **`sugerir_distribucion_automatica()`**: Algoritmo greedy para distribución óptima

#### Endpoints

**POST `/api/v1/lotes/recepcion`**
- Recepciona lote con validación de capacidad
- Si excede: retorna 409 Conflict con sugerencias
- Si no hay capacidad en sucursal: retorna 507 Insufficient Storage

**POST `/api/v1/lotes/recepcion-distribuida`**
- Recepciona lote distribuyendo entre múltiples bodegas
- Crea sub-lotes con sufijos por bodega
- Valida capacidad de todas las bodegas involucradas

### Frontend (React/TypeScript)

#### Componentes
- **`CapacidadDialog`**: Modal interactivo para visualizar y modificar distribución sugerida

#### Servicios
- **`LotesService.recepcionLote()`**: Método para recepción normal
- **`LotesService.recepcionDistribuida()`**: Método para recepción distribuida

## 📝 Ejemplo de Integración

```typescript
import { useState } from "react"
import { LotesService, type RecepcionLotePayload } from "@/client/LotesService"
import { CapacidadDialog } from "@/components/Recepciones/CapacidadDialog"
import useCustomToast from "@/hooks/useCustomToast"

function RecepcionForm() {
  const [capacidadError, setCapacidadError] = useState<any>(null)
  const [payloadOriginal, setPayloadOriginal] = useState<RecepcionLotePayload | null>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleSubmitRecepcion = async (payload: RecepcionLotePayload) => {
    try {
      // Guardar payload para uso posterior
      setPayloadOriginal(payload)
      
      // Intentar recepción normal
      const response = await LotesService.recepcionLote({ requestBody: payload })
      showSuccessToast("Éxito", `Lote ${response.lote.numero_lote} recepcionado correctamente`)
      
    } catch (error: any) {
      // Verificar si es error de capacidad (409)
      if (error.status === 409 && error.body?.error === "capacidad_insuficiente") {
        // Mostrar diálogo con sugerencias
        setCapacidadError(error.body)
      } 
      // Error de capacidad total en sucursal (507)
      else if (error.status === 507) {
        showErrorToast("Error", error.body.message || "No hay capacidad en toda la sucursal")
      } 
      else {
        showErrorToast("Error", "Error al recepcionar lote")
      }
    }
  }

  const handleConfirmarDistribucion = async (distribucion: BodegaDistribucion[]) => {
    if (!payloadOriginal) return

    try {
      // Crear payload de recepción distribuida
      const distribuciones = distribucion.map((bodega) => ({
        id_bodega: bodega.id_bodega,
        items: dividirProductosPorBodega(payloadOriginal.items, bodega.cantidad, distribucion)
      }))

      const payload = {
        lote_base: payloadOriginal.lote,
        distribuciones: distribuciones
      }

      // Ejecutar recepción distribuida
      const response = await LotesService.recepcionDistribuida({ requestBody: payload })
      
      showSuccessToast(
        "Éxito", 
        `Lote ${response.numero_lote_base} distribuido en ${response.bodegas_utilizadas} bodegas`
      )
      
      // Cerrar diálogo
      setCapacidadError(null)
      setPayloadOriginal(null)
      
    } catch (error: any) {
      if (error.status === 409) {
        showErrorToast("Error", error.body.message || "Capacidad insuficiente al distribuir")
      } else {
        showErrorToast("Error", "Error al distribuir lote")
      }
    }
  }

  const handleCancelarDistribucion = () => {
    setCapacidadError(null)
    setPayloadOriginal(null)
  }

  return (
    <>
      {/* Tu formulario existente */}
      <form onSubmit={handleSubmitRecepcion}>
        {/* ... campos del formulario ... */}
      </form>

      {/* Diálogo de capacidad */}
      {capacidadError && payloadOriginal && (
        <CapacidadDialog
          error={capacidadError}
          productosOriginales={payloadOriginal.items}
          onConfirm={handleConfirmarDistribucion}
          onCancel={handleCancelarDistribucion}
        />
      )}
    </>
  )
}

// Función auxiliar para dividir productos entre bodegas
function dividirProductosPorBodega(
  items: RecepcionProductoItem[],
  cantidadBodega: number,
  todasBodegas: BodegaDistribucion[]
): RecepcionProductoItem[] {
  // Implementación simplificada: divide proporcionalmente
  const totalGeneral = todasBodegas.reduce((sum, b) => sum + b.cantidad, 0)
  const proporcion = cantidadBodega / totalGeneral

  return items.map(item => ({
    ...item,
    cantidad: Math.round(item.cantidad * proporcion)
  }))
}
```

## 🔒 Manejo de Concurrencia

### Nivel Base de Datos (PostgreSQL)
```python
# Usa SELECT FOR UPDATE para locks pesimistas
stmt = (
    select(func.sum(Producto.cantidad_total))
    .where(Lote.id_bodega == bodega_id)
    .with_for_update()  # 🔒 Lock hasta commit
)
```

### Ventajas
- ✅ Previene race conditions
- ✅ Garantiza consistencia transaccional
- ✅ No requiere infraestructura adicional (Redis, etc.)
- ✅ PostgreSQL optimiza locks automáticamente

## 📊 Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────────┐
│ Usuario intenta recepcionar lote en Bodega A                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend calcula ocupación actual de Bodega A (con lock)         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├─── ✅ HAY CAPACIDAD ───────────────────┐
                 │                                         │
                 │                                         ▼
                 │                         ┌────────────────────────┐
                 │                         │ Crear lote en Bodega A │
                 │                         │ Retornar 200 OK        │
                 │                         └────────────────────────┘
                 │
                 └─── ❌ NO HAY CAPACIDAD ───────────────┐
                                                          │
                                                          ▼
                            ┌──────────────────────────────────────┐
                            │ Buscar bodegas alternativas          │
                            │ en misma sucursal                    │
                            └────────────┬─────────────────────────┘
                                         │
                                         ├─── ✅ HAY ALTERNATIVAS ───┐
                                         │                            │
                                         │                            ▼
                                         │          ┌────────────────────────────┐
                                         │          │ Calcular distribución      │
                                         │          │ Retornar 409 + sugerencias │
                                         │          └────────┬───────────────────┘
                                         │                   │
                                         │                   ▼
                                         │          ┌────────────────────────────┐
                                         │          │ Frontend muestra diálogo   │
                                         │          │ Usuario acepta/modifica    │
                                         │          └────────┬───────────────────┘
                                         │                   │
                                         │                   ▼
                                         │          ┌────────────────────────────┐
                                         │          │ POST /recepcion-distribuida│
                                         │          │ Crear sub-lotes            │
                                         │          │ Retornar 200 OK            │
                                         │          └────────────────────────────┘
                                         │
                                         └─── ❌ NO HAY CAPACIDAD EN SUCURSAL ───┐
                                                                                   │
                                                                                   ▼
                                                                  ┌────────────────────────┐
                                                                  │ Retornar 507           │
                                                                  │ Insufficient Storage   │
                                                                  └────────────────────────┘
```

## 🧪 Casos de Prueba

### 1. Recepción Normal (Capacidad Suficiente)
```bash
POST /api/v1/lotes/recepcion
{
  "lote": { "id_bodega": 1, ... },
  "items": [{ "cantidad": 50, ... }]
}

# Bodega tiene capacidad 100, ocupación 30
# 30 + 50 = 80 < 100 ✅
# Response: 200 OK
```

### 2. Capacidad Insuficiente (Con Alternativas)
```bash
POST /api/v1/lotes/recepcion
{
  "lote": { "id_bodega": 1, ... },
  "items": [{ "cantidad": 100, ... }]
}

# Bodega A: capacidad 100, ocupación 80, disponible 20
# Necesita: 100 > 20 ❌
# Bodega B (misma sucursal): disponible 50
# Bodega C (misma sucursal): disponible 40

# Response: 409 Conflict
{
  "detail": {
    "error": "capacidad_insuficiente",
    "excedente": 80,
    "sugerencias_distribucion": {
      "bodega_principal": { "cantidad_sugerida": 20 },
      "bodegas_secundarias": [
        { "id_bodega": 2, "cantidad": 50 },
        { "id_bodega": 3, "cantidad": 30 }
      ]
    }
  }
}
```

### 3. Recepción Distribuida
```bash
POST /api/v1/lotes/recepcion-distribuida
{
  "lote_base": { ... },
  "distribuciones": [
    { "id_bodega": 1, "items": [{ "cantidad": 20, ... }] },
    { "id_bodega": 2, "items": [{ "cantidad": 50, ... }] },
    { "id_bodega": 3, "items": [{ "cantidad": 30, ... }] }
  ]
}

# Response: 200 OK
{
  "numero_lote_base": "LOT-2025-001",
  "lotes_creados": [
    { "numero_lote": "LOT-2025-001-BOD", "bodega": "Principal" },
    { "numero_lote": "LOT-2025-001-SEC", "bodega": "Secundaria A" },
    { "numero_lote": "LOT-2025-001-TRA", "bodega": "Tránsito" }
  ],
  "total_productos": 3,
  "bodegas_utilizadas": 3
}
```

## 📈 Métricas y Monitoreo

### Queries Útiles
```sql
-- Ocupación actual de una bodega
SELECT 
  b.nombre,
  b.capacidad,
  COALESCE(SUM(p.cantidad_total), 0) as ocupacion,
  b.capacidad - COALESCE(SUM(p.cantidad_total), 0) as disponible,
  ROUND((COALESCE(SUM(p.cantidad_total), 0)::float / b.capacidad * 100), 2) as porcentaje_ocupacion
FROM bodega b
LEFT JOIN lote l ON l.id_bodega = b.id_bodega AND l.estado IN ('Activo', 'En tránsito')
LEFT JOIN producto p ON p.id_lote = l.id_lote
WHERE b.id_bodega = 1
GROUP BY b.id_bodega, b.nombre, b.capacidad;

-- Bodegas críticas (>90% ocupación)
SELECT 
  b.nombre,
  ROUND((ocupacion::float / capacidad * 100), 2) as porcentaje
FROM (
  SELECT 
    b.id_bodega,
    b.nombre,
    b.capacidad,
    COALESCE(SUM(p.cantidad_total), 0) as ocupacion
  FROM bodega b
  LEFT JOIN lote l ON l.id_bodega = b.id_bodega AND l.estado IN ('Activo', 'En tránsito')
  LEFT JOIN producto p ON p.id_lote = l.id_lote
  GROUP BY b.id_bodega, b.nombre, b.capacidad
) as ocupacion_bodegas
WHERE ocupacion::float / capacidad > 0.9
ORDER BY porcentaje DESC;
```

## 🚀 Deploy

### 1. Aplicar cambios en backend
```bash
cd backend
uv run uvicorn app.main:app --reload
```

### 2. Regenerar cliente frontend (opcional)
```bash
cd frontend
npm run generate-client
```

### 3. Compilar frontend
```bash
npm run build
```

## ✅ Checklist de Implementación

- [x] Funciones auxiliares backend (`calcular_ocupacion_bodega`, etc.)
- [x] Endpoint `/lotes/recepcion` con validación
- [x] Endpoint `/lotes/recepcion-distribuida`
- [x] Exception personalizada `CapacidadInsuficienteError`
- [x] Componente `CapacidadDialog` frontend
- [x] Actualización `LotesService.ts` con nuevos métodos
- [ ] Integrar diálogo en `RecepcionForm.tsx`
- [ ] Tests unitarios backend
- [ ] Tests E2E frontend
- [ ] Documentación de API (OpenAPI)

## 🔧 Próximas Mejoras

1. **Dashboard de Capacidad**: Visualización en tiempo real de ocupación de bodegas
2. **Alertas Proactivas**: Notificaciones cuando bodega llega a 80% ocupación
3. **Algoritmos Avanzados**: Optimización considerando distancia física, temperatura, etc.
4. **Histórico**: Gráficas de tendencia de ocupación
5. **Predicción**: ML para predecir necesidades futuras de capacidad

---

**Autor**: Sistema Pyllren  
**Fecha**: Octubre 2025  
**Versión**: 1.0.1
