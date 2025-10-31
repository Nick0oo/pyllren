from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep, get_current_admin_user, get_user_scope, is_admin_user
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key, stats_cache_key
)
from app.models import (
    Bodega,
    BodegaCreate,
    BodegaPublic,
    BodegaPublicExtended,
    BodegasPublic,
    BodegaUpdate,
    Message,
    Sucursal,
    Lote,
    Producto,
)

router = APIRouter(prefix="/bodegas", tags=["bodegas"])


@router.get("/", response_model=BodegasPublic)
def read_bodegas(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    tipo: str | None = None,
    estado: bool | None = None,
    id_sucursal: int | None = None,
) -> Any:
    """
    Retrieve bodegas with search and filters.
    Admins see all and can filter by id_sucursal.
    Non-admins see only bodegas from their sucursal (id_sucursal parameter is ignored).
    """
    scope = get_user_scope(current_user)
    is_admin = is_admin_user(current_user)
    
    # Determinar id_sucursal para filtrar
    if is_admin:
        # Admin puede usar id_sucursal del query (opcional)
        filter_sucursal_id = id_sucursal
    else:
        # No-admin: ignorar id_sucursal del query, usar su sucursal automáticamente
        filter_sucursal_id = scope["id_sucursal"] if scope else None  # type: ignore[index]
    
    # Generate cache key including all filters
    cache_key = list_cache_key(
        "bodegas",
        skip=skip,
        limit=limit,
        q=q,
        tipo=tipo,
        estado=estado,
        id_sucursal=filter_sucursal_id,
        is_admin=is_admin,
    )
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return BodegasPublic(**cached_result)
    
    # Construir query base
    count_statement = select(func.count()).select_from(Bodega)
    statement = select(Bodega)
    
    # Aplicar filtros
    filters = []
    
    # Filtro por sucursal
    if filter_sucursal_id is not None:
        filters.append(Bodega.id_sucursal == filter_sucursal_id)
    
    # Filtro por tipo
    if tipo:
        filters.append(Bodega.tipo == tipo)
    
    # Filtro por estado
    if estado is not None:
        filters.append(Bodega.estado == estado)
    
    # Búsqueda por nombre, tipo o ubicación
    if q:
        search_filter = or_(
            Bodega.nombre.ilike(f"%{q}%"),
            Bodega.tipo.ilike(f"%{q}%"),
            Bodega.ubicacion.ilike(f"%{q}%"),  # type: ignore
        )
        filters.append(search_filter)
    
    # Aplicar todos los filtros
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    
    # Ejecutar queries
    count = session.exec(count_statement).one()
    statement = statement.offset(skip).limit(limit)
    bodegas = session.exec(statement).all()
    
    result = BodegasPublic(data=bodegas, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get(
    "/stats",
    dependencies=[Depends(get_current_admin_user)]
)
def get_bodegas_stats(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get bodegas statistics. Only admins can access this endpoint.
    Returns: total_bodegas, operativas, capacidad_total, ocupacion_total
    """
    # Generate cache key
    cache_key = stats_cache_key("bodegas")
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Total bodegas
    total_bodegas = session.exec(select(func.count()).select_from(Bodega)).one()
    
    # Bodegas operativas (estado=True)
    operativas = session.exec(
        select(func.count()).select_from(Bodega).where(Bodega.estado == True)
    ).one()
    
    # Capacidad total (suma de todas las capacidades)
    capacidad_total_result = session.exec(
        select(func.sum(Bodega.capacidad)).select_from(Bodega)
    ).one()
    capacidad_total = capacidad_total_result if capacidad_total_result is not None else 0
    
    # Ocupación total básica (placeholder por ahora)
    # En el futuro se puede calcular sumando ocupación de todas las bodegas
    ocupacion_total = 0.0  # Placeholder básico
    
    result = {
        "total_bodegas": total_bodegas,
        "operativas": operativas,
        "capacidad_total": capacidad_total,
        "ocupacion_total": ocupacion_total
    }
    
    # Cache the result (TTL: 1 minute)
    set_cache(cache_key, result, ttl=60)
    
    return result


@router.get("/{id}", response_model=BodegaPublicExtended)
def read_bodega(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get bodega by ID with extended information (total lotes, productos, sucursal).
    Non-admins can only see bodegas from their sucursal.
    """
    # Aplicar scope de seguridad
    scope = get_user_scope(current_user)
    is_admin = is_admin_user(current_user)
    
    # Generate cache key
    cache_key = item_cache_key("bodegas", id)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        # Verificar scope antes de retornar cache
        if not is_admin and cached_result.get("id_sucursal") != scope.get("id_sucursal"):  # type: ignore[index]
            raise HTTPException(status_code=403, detail="Bodega fuera de alcance para el usuario")
        return BodegaPublicExtended(**cached_result)
    
    bodega = session.get(Bodega, id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")
    
    # Verificar scope de seguridad
    if not is_admin:
        if scope is None or bodega.id_sucursal != scope["id_sucursal"]:  # type: ignore[index]
            raise HTTPException(status_code=403, detail="Bodega fuera de alcance para el usuario")
    
    # Calcular total_lotes
    total_lotes = session.exec(
        select(func.count()).select_from(Lote).where(Lote.id_bodega == id)
    ).one()
    
    # Calcular total_productos: contar productos de lotes asociados a esta bodega
    total_productos = session.exec(
        select(func.count())
        .select_from(Producto)
        .join(Lote, Producto.id_lote == Lote.id_lote)
        .where(Lote.id_bodega == id)
    ).one()
    
    # Obtener nombre de sucursal
    sucursal_nombre = None
    if bodega.sucursal:
        sucursal_nombre = bodega.sucursal.nombre
    else:
        # Si no está cargada la relación, obtenerla manualmente
        sucursal = session.get(Sucursal, bodega.id_sucursal)
        if sucursal:
            sucursal_nombre = sucursal.nombre
    
    # Construir respuesta extendida
    result_data = bodega.model_dump()
    result_data["total_lotes"] = total_lotes
    result_data["total_productos"] = total_productos
    result_data["sucursal_nombre"] = sucursal_nombre
    
    result = BodegaPublicExtended(**result_data)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.post(
    "/",
    dependencies=[Depends(get_current_admin_user)],
    response_model=BodegaPublic
)
def create_bodega(
    *, session: SessionDep, current_user: CurrentUser, bodega_in: BodegaCreate
) -> Any:
    """
    Create new bodega. Only admins can create bodegas.
    """
    # Validar que id_sucursal existe
    sucursal = session.get(Sucursal, bodega_in.id_sucursal)
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal not found")
    
    # Validaciones de rangos
    if bodega_in.temperatura_min is not None and bodega_in.temperatura_max is not None:
        if bodega_in.temperatura_min >= bodega_in.temperatura_max:
            raise HTTPException(
                status_code=400,
                detail="temperatura_min debe ser menor que temperatura_max"
            )
    
    if bodega_in.humedad_min is not None and bodega_in.humedad_max is not None:
        if bodega_in.humedad_min >= bodega_in.humedad_max:
            raise HTTPException(
                status_code=400,
                detail="humedad_min debe ser menor que humedad_max"
            )
    
    if bodega_in.humedad_min is not None:
        if bodega_in.humedad_min < 0 or bodega_in.humedad_min > 100:
            raise HTTPException(
                status_code=400,
                detail="humedad_min debe estar entre 0 y 100"
            )
    
    if bodega_in.humedad_max is not None:
        if bodega_in.humedad_max < 0 or bodega_in.humedad_max > 100:
            raise HTTPException(
                status_code=400,
                detail="humedad_max debe estar entre 0 y 100"
            )
    
    # Validar capacidad > 0 (ya validado por Pydantic pero doble verificación)
    if bodega_in.capacidad <= 0:
        raise HTTPException(status_code=400, detail="capacidad debe ser mayor a 0")
    
    bodega = Bodega.model_validate(bodega_in)
    session.add(bodega)
    session.commit()
    session.refresh(bodega)
    
    # Invalidate cache
    invalidate_entity_cache("bodegas")
    
    return bodega


@router.put("/{id}", response_model=BodegaPublic)
def update_bodega(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    bodega_in: BodegaUpdate,
) -> Any:
    """
    Update a bodega.
    Non-admins can only update bodegas from their sucursal.
    Admins can update any bodega.
    """
    bodega = session.get(Bodega, id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")
    
    # Aplicar scope de seguridad
    scope = get_user_scope(current_user)
    is_admin = is_admin_user(current_user)
    
    if not is_admin:
        if scope is None or bodega.id_sucursal != scope["id_sucursal"]:  # type: ignore[index]
            raise HTTPException(status_code=403, detail="Bodega fuera de alcance para el usuario")
    
    # Validar que id_sucursal existe si se está actualizando
    update_dict = bodega_in.model_dump(exclude_unset=True)
    if "id_sucursal" in update_dict:
        sucursal = session.get(Sucursal, update_dict["id_sucursal"])
        if not sucursal:
            raise HTTPException(status_code=404, detail="Sucursal not found")
    
    # Validaciones de rangos
    temperatura_min = update_dict.get("temperatura_min", bodega.temperatura_min)
    temperatura_max = update_dict.get("temperatura_max", bodega.temperatura_max)
    
    if temperatura_min is not None and temperatura_max is not None:
        if temperatura_min >= temperatura_max:
            raise HTTPException(
                status_code=400,
                detail="temperatura_min debe ser menor que temperatura_max"
            )
    
    humedad_min = update_dict.get("humedad_min", bodega.humedad_min)
    humedad_max = update_dict.get("humedad_max", bodega.humedad_max)
    
    if humedad_min is not None and humedad_max is not None:
        if humedad_min >= humedad_max:
            raise HTTPException(
                status_code=400,
                detail="humedad_min debe ser menor que humedad_max"
            )
    
    if humedad_min is not None:
        if humedad_min < 0 or humedad_min > 100:
            raise HTTPException(
                status_code=400,
                detail="humedad_min debe estar entre 0 y 100"
            )
    
    if humedad_max is not None:
        if humedad_max < 0 or humedad_max > 100:
            raise HTTPException(
                status_code=400,
                detail="humedad_max debe estar entre 0 y 100"
            )
    
    # Validar capacidad si se está actualizando
    if "capacidad" in update_dict and update_dict["capacidad"] <= 0:
        raise HTTPException(status_code=400, detail="capacidad debe ser mayor a 0")
    
    bodega.sqlmodel_update(update_dict)
    session.add(bodega)
    session.commit()
    session.refresh(bodega)
    
    # Invalidate cache
    invalidate_entity_cache("bodegas")
    
    return bodega


@router.delete("/{id}")
def delete_bodega(session: SessionDep, current_user: CurrentUser, id: int) -> Message:
    """
    Delete a bodega (soft delete).
    Non-admins can only delete bodegas from their sucursal.
    Admins can delete any bodega.
    """
    bodega = session.get(Bodega, id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")
    
    # Aplicar scope de seguridad
    scope = get_user_scope(current_user)
    is_admin = is_admin_user(current_user)
    
    if not is_admin:
        if scope is None or bodega.id_sucursal != scope["id_sucursal"]:  # type: ignore[index]
            raise HTTPException(status_code=403, detail="Bodega fuera de alcance para el usuario")
    
    bodega.estado = False
    session.add(bodega)
    session.commit()
    
    # Invalidate cache
    invalidate_entity_cache("bodegas")
    
    return Message(message="Bodega deleted successfully")

