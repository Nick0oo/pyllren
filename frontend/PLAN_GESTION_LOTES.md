# Plan de Implementación: Página de Gestión de Lotes

## 📋 Resumen Ejecutivo

Este documento detalla cómo establecer una nueva página para la gestión de lotes en el frontend, siguiendo los patrones arquitectónicos existentes en el proyecto (similar a las páginas de Proveedores e Items).

## 🔍 Análisis de la Estructura Actual

### Patrón Identificado

El proyecto sigue una arquitectura consistente:

1. **Rutas**: TanStack Router con rutas en `routes/_layout/`
2. **Componentes**: Organizados por entidad en `components/[Entidad]/`
3. **Servicios**: Cliente manual en `client/[Entidad]Service.ts`
4. **UI**: Chakra UI con componentes reutilizables

### Modelo de Datos: Lote

#### Campos del Modelo
```typescript
{
  id_lote: number
  numero_lote: string
  fecha_fabricacion: date
  fecha_vencimiento: date
  estado: "Activo" | "Vencido" | "Devuelto" | "En tránsito"
  observaciones?: string
  id_proveedor: number
  id_bodega: number
  fecha_registro: datetime
}
```

#### Endpoints Disponibles (Backend)
- `GET /api/v1/lotes/` - Listar lotes (con paginación)
- `GET /api/v1/lotes/{id}` - Obtener lote por ID
- `POST /api/v1/lotes/` - Crear nuevo lote
- `PUT /api/v1/lotes/{id}` - Actualizar lote
- ⚠️ **DELETE no implementado** - Será necesario agregarlo si se requiere eliminación

### Dependencias Relacionadas

Los lotes tienen relaciones con:
- **Proveedores**: `id_proveedor` (FK)
- **Bodegas**: `id_bodega` (FK)

Necesitarás endpoints o servicios para:
- Listar proveedores (ya existe: `ProveedoresService`)
- Listar bodegas (probablemente necesites crear `BodegasService`)

## 📁 Archivos a Crear

### 1. Servicio del Cliente

**Ubicación**: `frontend/src/client/LotesService.ts`

```typescript
// Patrón similar a ProveedoresService.ts
// Debe incluir métodos para:
// - readLotes({ skip, limit })
// - readLote({ id })
// - createLote({ requestBody })
// - updateLote({ id, requestBody })
```

**Interfaces necesarias**:
- `LoteCreate`
- `LoteUpdate`
- `LotePublic`
- `LotesPublic`

### 2. Componentes de la Carpeta `Lotes/`

**Ubicación**: `frontend/src/components/Lotes/`

#### 2.1. `AddLote.tsx`
- Formulario modal/dialog para crear lotes
- Campos: numero_lote, fecha_fabricacion, fecha_vencimiento, estado, observaciones
- Selectores para: id_proveedor, id_bodega
- Validaciones con react-hook-form
- Uso de mutation para crear

#### 2.2. `EditLote.tsx`
- Formulario similar a AddLote pero pre-llenado
- Actualización con PUT
- Validaciones

#### 2.3. `DeleteLote.tsx`
- Dialog de confirmación
- ⚠️ **Nota**: Requiere endpoint DELETE en backend

#### 2.4. `LoteActionsMenu.tsx`
- Menú de tres puntos (vertical)
- Opciones: Editar, Eliminar
- Similar a `ProveedorActionsMenu.tsx`

### 3. Componente de Loading

**Ubicación**: `frontend/src/components/Pending/PendingLotes.tsx`

- Skeleton para tabla de lotes
- Skeleton para cards de métricas (si aplica)
- Similar a `PendingProveedores.tsx`

### 4. Página Principal

**Ubicación**: `frontend/src/routes/_layout/lotes.tsx`

**Estructura esperada**:
```typescript
- Header con título y botón "Agregar Lote"
- Cards de métricas (opcional):
  - Total Lotes
  - Lotes Activos
  - Lotes Vencidos
  - Lotes Próximos a Vencer
- Barra de búsqueda/filtros (opcional)
- Tabla de lotes con:
  - Columnas: Número Lote, Proveedor, Bodega, Fecha Fabricación, 
    Fecha Vencimiento, Estado, Productos, Acciones
  - Paginación
- Manejo de estados vacíos
```

### 5. Actualización del Menú

**Archivo**: `frontend/src/components/Common/SidebarItems.tsx`

Agregar:
```typescript
import { FiPackage } from "react-icons/fi"

// En adminItems o items:
{ icon: FiPackage, title: "Lotes", path: "/lotes" }
```

## 🔧 Pasos de Implementación

### Paso 1: Crear el Servicio del Cliente
1. Crear `LotesService.ts` basado en `ProveedoresService.ts`
2. Definir interfaces TypeScript
3. Implementar métodos HTTP usando el cliente OpenAPI

### Paso 2: Crear Componentes de UI
1. Crear carpeta `components/Lotes/`
2. Implementar `AddLote.tsx` (referencia: `AddProveedor.tsx`)
3. Implementar `EditLote.tsx` (referencia: `EditProveedor.tsx`)
4. Implementar `DeleteLote.tsx` (si se requiere)
5. Implementar `LoteActionsMenu.tsx`

### Paso 3: Crear Componente de Loading
1. Crear `PendingLotes.tsx` (referencia: `PendingProveedores.tsx`)

### Paso 4: Crear la Página Principal
1. Crear `routes/_layout/lotes.tsx`
2. Implementar tabla con paginación
3. Integrar componentes Add/Edit/Delete
4. Agregar métricas/stats (si hay endpoint disponible)

### Paso 5: Actualizar Navegación
1. Agregar enlace en `SidebarItems.tsx`
2. Verificar permisos si aplica

### Paso 6: Validaciones y Testing
1. Validar formularios
2. Manejar errores de API
3. Probar flujos completos (CRUD)

## 🎨 Consideraciones de UX/UI

### Campos Especiales

1. **Fechas**: Usar input type="date" o un date picker
2. **Estado**: Select con opciones predefinidas
3. **Proveedor/Bodega**: Selectores que carguen datos de otros servicios
4. **Validaciones**:
   - `fecha_vencimiento` debe ser > `fecha_fabricacion`
   - `numero_lote` debe ser único (validar en backend)

### Estados de Lotes

- **Activo**: Verde
- **Vencido**: Rojo
- **Devuelto**: Naranja/Amarillo
- **En tránsito**: Azul

### Indicadores Visuales

- Badges de color para estados
- Alertas para lotes próximos a vencer (< 30 días)
- Indicadores de stock/productos asociados

## 🔌 Integraciones Necesarias

### Servicios Adicionales

1. **BodegasService** (si no existe):
   - Necesario para el selector de bodegas en formularios
   - Endpoint: `GET /api/v1/bodegas/`

2. **ProveedoresService** (ya existe):
   - Para el selector de proveedores en formularios

### Endpoints Adicionales Recomendados

1. **Stats/Métricas**:
   - `GET /api/v1/lotes/stats` - Estadísticas de lotes
   - Retornar: total, activos, vencidos, próximos a vencer

2. **Búsqueda/Filtros**:
   - Extender `GET /api/v1/lotes/` con parámetros:
     - `q`: búsqueda por texto
     - `estado`: filtrar por estado
     - `id_proveedor`: filtrar por proveedor
     - `fecha_vencimiento`: filtrar por rango

3. **DELETE**:
   - `DELETE /api/v1/lotes/{id}` - Si se requiere eliminación

## 📝 Ejemplo de Estructura de Código

### Ejemplo: LotesService.ts
```typescript
import type { CancelablePromise } from './core/CancelablePromise'
import { OpenAPI } from './core/OpenAPI'
import { request as __request } from './core/request'

export interface LoteCreate {
  numero_lote: string
  fecha_fabricacion: string // ISO date string
  fecha_vencimiento: string // ISO date string
  estado: string
  observaciones?: string
  id_proveedor: number
  id_bodega: number
}

export interface LoteUpdate {
  numero_lote?: string
  fecha_fabricacion?: string
  fecha_vencimiento?: string
  estado?: string
  observaciones?: string
  id_proveedor?: number
  id_bodega?: number
}

export interface LotePublic {
  id_lote: number
  numero_lote: string
  fecha_fabricacion: string
  fecha_vencimiento: string
  estado: string
  observaciones?: string
  id_proveedor: number
  id_bodega: number
  fecha_registro: string
}

export interface LotesPublic {
  data: LotePublic[]
  count: number
}

export class LotesService {
  public static readLotes(data: {
    skip?: number
    limit?: number
  }): CancelablePromise<LotesPublic> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/lotes/',
      query: {
        skip: data.skip,
        limit: data.limit,
      },
    })
  }

  public static readLote(data: { id: number }): CancelablePromise<LotePublic> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `/api/v1/lotes/${data.id}`,
    })
  }

  public static createLote(data: {
    requestBody: LoteCreate
  }): CancelablePromise<LotePublic> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/lotes/',
      body: data.requestBody,
      mediaType: 'application/json',
    })
  }

  public static updateLote(data: {
    id: number
    requestBody: LoteUpdate
  }): CancelablePromise<LotePublic> {
    return __request(OpenAPI, {
      method: 'PUT',
      url: `/api/v1/lotes/${data.id}`,
      body: data.requestBody,
      mediaType: 'application/json',
    })
  }
}
```

## ✅ Checklist de Implementación

- [ ] Crear `LotesService.ts` con todas las interfaces y métodos
- [ ] Crear `PendingLotes.tsx`
- [ ] Crear `AddLote.tsx` con validaciones
- [ ] Crear `EditLote.tsx` con prellenado de datos
- [ ] Crear `DeleteLote.tsx` (o marcarlo como futuro)
- [ ] Crear `LoteActionsMenu.tsx`
- [ ] Crear `routes/_layout/lotes.tsx` con tabla y paginación
- [ ] Agregar enlace en `SidebarItems.tsx`
- [ ] Implementar métricas/stats (si hay endpoint)
- [ ] Agregar búsqueda/filtros (opcional)
- [ ] Probar flujos completos
- [ ] Validar permisos de acceso
- [ ] Documentar código

## 🚀 Próximos Pasos

1. **Inmediato**: Crear la estructura base (servicio y página principal)
2. **Corto plazo**: Implementar CRUD completo
3. **Mediano plazo**: Agregar métricas y filtros avanzados
4. **Largo plazo**: Integración con productos (mostrar productos por lote)

## 📚 Referencias

- Página similar de referencia: `routes/_layout/proveedores.tsx`
- Componente similar: `components/Proveedores/`
- Servicio similar: `client/ProveedoresService.ts`

---

**Nota**: Este plan sigue los patrones establecidos en el proyecto. Cualquier desviación debe ser justificada y documentada.

