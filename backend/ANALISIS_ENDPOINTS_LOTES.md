# Análisis y Propuesta: Endpoints de Lotes

## 📋 Estado Actual

### Endpoints Existentes
- ✅ `GET /api/v1/lotes/` - Lista básica (sin filtros)
- ✅ `GET /api/v1/lotes/{id}` - Obtener lote por ID
- ✅ `POST /api/v1/lotes/` - Crear lote
- ✅ `PUT /api/v1/lotes/{id}` - Actualizar lote
- ❌ `GET /api/v1/lotes/stats` - **NO EXISTE** (el frontend lo está llamando)
- ❌ `DELETE /api/v1/lotes/{id}` - No existe

## 🎯 Necesidades del Frontend

Según el análisis del código frontend (`lotes.tsx`), se requieren:

### 1. GET `/api/v1/lotes/` - Mejoras Necesarias

**Filtros requeridos:**
- `q` (string, opcional): Búsqueda por número de lote
- `estado` (string, opcional): Filtrar por estado ("Activo", "Vencido", "Devuelto", "En tránsito")
- `id_bodega` (int, opcional): Filtrar por bodega
- `id_proveedor` (int, opcional): Filtrar por proveedor
- `skip` (int): Paginación offset
- `limit` (int): Paginación limit

**Lógica de "Próximos a vencer":**
- El frontend calcula client-side lotes con menos de 30 días para vencer
- **Propuesta**: Mejor hacerlo en el backend para eficiencia

### 2. GET `/api/v1/lotes/stats` - Nuevo Endpoint

**Estadísticas necesarias:**
```python
{
    "total_lotes": int,
    "activos": int,
    "vencidos": int,
    "próximos_a_vencer": int  # Lotes que vencen en < 30 días
}
```

**Implementación sugerida:**
- Usar cache similar a `proveedores/stats`
- Calcular "próximos a vencer" en el backend (días configurables)

### 3. DELETE `/api/v1/lotes/{id}` - Opcional

**Consideraciones:**
- ¿Soft delete o hard delete?
- Si hay productos asociados, ¿qué hacer?
- Mirar el patrón de otros endpoints (bodegas tiene soft delete)

## 🔧 Propuestas de Implementación

### Opción 1: Endpoint GET Mejorado con Filtros

```python
@router.get("/", response_model=LotesPublic)
def read_lotes(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,  # Búsqueda por número de lote
    estado: str | None = None,  # Filtro por estado
    id_bodega: int | None = None,  # Filtro por bodega
    id_proveedor: int | None = None,  # Filtro por proveedor
    proximos_vencer: bool | None = None,  # Lotes próximos a vencer (< 30 días)
) -> Any:
    """
    Retrieve lotes with optional filters.
    """
    # Construir query base
    statement = select(Lote)
    
    # Aplicar filtros
    if q:
        statement = statement.where(Lote.numero_lote.contains(q))
    
    if estado:
        statement = statement.where(Lote.estado == estado)
    
    if id_bodega:
        statement = statement.where(Lote.id_bodega == id_bodega)
    
    if id_proveedor:
        statement = statement.where(Lote.id_proveedor == id_proveedor)
    
    if proximos_vencer:
        from datetime import date, timedelta
        fecha_limite = date.today() + timedelta(days=30)
        statement = statement.where(
            Lote.fecha_vencimiento <= fecha_limite,
            Lote.fecha_vencimiento > date.today(),
            Lote.estado == "Activo"
        )
    
    # Contar total
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()
    
    # Aplicar paginación
    statement = statement.offset(skip).limit(limit)
    lotes = session.exec(statement).all()
    
    return LotesPublic(data=lotes, count=count)
```

### Opción 2: Endpoint de Estadísticas

```python
@router.get("/stats", response_model=dict)
def get_lotes_stats(
    session: SessionDep,
    current_user: CurrentUser,
    dias_vencimiento: int = 30  # Configurable
) -> Any:
    """
    Get lotes statistics.
    """
    from datetime import date, timedelta
    
    # Cache key
    cache_key = f"lotes:stats:{dias_vencimiento}"
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Total lotes
    total_lotes = session.exec(select(func.count()).select_from(Lote)).one()
    
    # Lotes activos
    activos = session.exec(
        select(func.count()).select_from(Lote).where(Lote.estado == "Activo")
    ).one()
    
    # Lotes vencidos
    fecha_hoy = date.today()
    vencidos = session.exec(
        select(func.count()).select_from(Lote).where(
            Lote.estado == "Vencido",
            # O: Lote.fecha_vencimiento < fecha_hoy
        )
    ).one()
    
    # Lotes próximos a vencer (activos que vencen en < X días)
    fecha_limite = fecha_hoy + timedelta(days=dias_vencimiento)
    proximos_a_vencer = session.exec(
        select(func.count()).select_from(Lote).where(
            Lote.estado == "Activo",
            Lote.fecha_vencimiento <= fecha_limite,
            Lote.fecha_vencimiento > fecha_hoy
        )
    ).one()
    
    result = {
        "total_lotes": total_lotes,
        "activos": activos,
        "vencidos": vencidos,
        "próximos_a_vencer": proximos_a_vencer
    }
    
    # Cache por 1 minuto
    set_cache(cache_key, result, ttl=60)
    
    return result
```

### Opción 3: Endpoint DELETE (Soft Delete)

```python
@router.delete("/{id}", response_model=Message)
def delete_lote(
    session: SessionDep,
    current_user: CurrentUser,
    id: int
) -> Any:
    """
    Delete a lote (soft delete by changing state).
    """
    lote = session.get(Lote, id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote not found")
    
    # Verificar si tiene productos asociados
    if lote.productos:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete lote with associated products"
        )
    
    # Soft delete: cambiar estado o eliminar
    session.delete(lote)
    session.commit()
    
    # Invalidar cache
    invalidate_entity_cache("lotes")
    invalidate_entity_cache("proveedores")
    
    return Message(message="Lote deleted successfully")
```

## 📊 Comparación con Proveedores

El endpoint de proveedores ya tiene:
- ✅ Filtros (`q`, `estado`)
- ✅ Estadísticas (`/stats`)
- ✅ Cache implementado

**Recomendación:** Seguir el mismo patrón para consistencia.

## 🎨 Mejoras Adicionales Sugeridas

### 1. Relaciones en LotePublic
Actualmente `LotePublic` solo tiene IDs. Podría incluir:
- `proveedor_nombre`: str (nombre del proveedor)
- `bodega_nombre`: str (nombre de la bodega)
- `total_productos`: int (cantidad de productos asociados)

### 2. Validaciones
- Verificar que `fecha_vencimiento > fecha_fabricacion`
- Verificar que el proveedor existe
- Verificar que la bodega existe
- Validar formato de `numero_lote` (único)

### 3. Endpoints Auxiliares
- `GET /lotes/by-proveedor/{id}` - Lotes de un proveedor
- `GET /lotes/by-bodega/{id}` - Lotes de una bodega
- `GET /lotes/proximos-vencer` - Lotes próximos a vencer con detalles

## ✅ Plan de Implementación Recomendado

**Prioridad Alta:**
1. ✅ Crear `/lotes/stats` endpoint (el frontend lo necesita ya)
2. ✅ Mejorar `GET /lotes/` con filtros básicos (`q`, `estado`, `id_bodega`)
3. ✅ Añadir validaciones en CREATE/UPDATE

**Prioridad Media:**
4. Añadir endpoint DELETE
5. Incluir nombres en LotePublic (proveedor_nombre, bodega_nombre)
6. Endpoint para lotes próximos a vencer

**Prioridad Baja:**
7. Endpoints auxiliares (by-proveedor, by-bodega)
8. Métricas adicionales en stats

## 🔍 Notas Técnicas

### Cache
- Usar `list_cache_key()` para listas filtradas (incluir filtros en la key)
- Cache de stats con TTL corto (60 segundos)
- Invalidar cache en CREATE/UPDATE/DELETE

### Performance
- Índices sugeridos en BD:
  - `numero_lote` (para búsquedas)
  - `estado`
  - `fecha_vencimiento` (para queries de próximos a vencer)
  - `id_bodega`, `id_proveedor` (FK ya tienen índices)

### Seguridad
- Validar permisos si es necesario
- Sanitizar inputs de búsqueda
- Validar rangos de fechas

