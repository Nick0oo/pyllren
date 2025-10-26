from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep, get_current_admin_user
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache, 
    list_cache_key, item_cache_key, stats_cache_key
)
from app.models import (
    Message,
    Proveedor,
    ProveedorCreate,
    ProveedorPublic,
    ProveedoresPublic,
    ProveedorUpdate,
)

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.get(
    "/",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedoresPublic
)
def read_proveedores(
    session: SessionDep, 
    current_user: CurrentUser, 
    skip: int = 0, 
    limit: int = 100,
    q: str | None = None,
    estado: bool | None = None
) -> Any:
    """
    Retrieve proveedores with optional search and filter.
    """
    # Generate cache key
    cache_key = list_cache_key("proveedores", skip=skip, limit=limit, q=q, estado=estado)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return ProveedoresPublic(**cached_result)
    
    # Construir query base
    statement = select(Proveedor)
    count_statement = select(func.count()).select_from(Proveedor)
    
    # Aplicar filtros
    filters = []
    
    if q:
        search_filter = or_(
            Proveedor.nombre.ilike(f"%{q}%"),
            Proveedor.nit.ilike(f"%{q}%"),
            Proveedor.email.ilike(f"%{q}%"),
            Proveedor.telefono.ilike(f"%{q}%")
        )
        filters.append(search_filter)
    
    if estado is not None:
        filters.append(Proveedor.estado == estado)
    
    # Aplicar filtros a ambas queries
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    
    # Ejecutar queries
    count = session.exec(count_statement).one()
    statement = statement.offset(skip).limit(limit)
    proveedores = session.exec(statement).all()
    
    result = ProveedoresPublic(data=proveedores, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get(
    "/stats",
    dependencies=[Depends(get_current_admin_user)]
)
def get_proveedores_stats(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get proveedores statistics.
    """
    # Generate cache key
    cache_key = stats_cache_key("proveedores")
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Total proveedores
    total_proveedores = session.exec(select(func.count()).select_from(Proveedor)).one()
    
    # Proveedores activos
    activos = session.exec(
        select(func.count()).select_from(Proveedor).where(Proveedor.estado == True)
    ).one()
    
    # Proveedores inactivos
    inactivos = session.exec(
        select(func.count()).select_from(Proveedor).where(Proveedor.estado == False)
    ).one()
    
    # Total lotes asociados (necesitamos importar Lote)
    from app.models import Lote
    total_lotes = session.exec(
        select(func.count()).select_from(Lote)
    ).one()
    
    result = {
        "total_proveedores": total_proveedores,
        "activos": activos,
        "inactivos": inactivos,
        "total_lotes": total_lotes
    }
    
    # Cache the result (TTL: 1 minute)
    set_cache(cache_key, result, ttl=60)
    
    return result


@router.get(
    "/{id}",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedorPublic
)
def read_proveedor(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get proveedor by ID.
    """
    # Generate cache key
    cache_key = item_cache_key("proveedores", id)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return ProveedorPublic(**cached_result)
    
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, proveedor.model_dump(), ttl=300)
    
    return proveedor


@router.post(
    "/",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedorPublic
)
def create_proveedor(
    *, session: SessionDep, current_user: CurrentUser, proveedor_in: ProveedorCreate
) -> Any:
    """
    Create new proveedor.
    """
    # Verificar que el NIT no esté duplicado
    existing_proveedor = session.exec(
        select(Proveedor).where(Proveedor.nit == proveedor_in.nit)
    ).first()
    
    if existing_proveedor:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe un proveedor con el NIT {proveedor_in.nit}"
        )
    
    proveedor = Proveedor.model_validate(proveedor_in)
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    
    # Invalidate cache
    invalidate_entity_cache("proveedores")
    
    return proveedor


@router.put(
    "/{id}",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedorPublic
)
def update_proveedor(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    proveedor_in: ProveedorUpdate,
) -> Any:
    """
    Update a proveedor.
    """
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    
    # Si se está actualizando el NIT, verificar que no esté duplicado
    if proveedor_in.nit and proveedor_in.nit != proveedor.nit:
        existing_proveedor = session.exec(
            select(Proveedor).where(Proveedor.nit == proveedor_in.nit)
        ).first()
        
        if existing_proveedor:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe un proveedor con el NIT {proveedor_in.nit}"
            )
    
    update_dict = proveedor_in.model_dump(exclude_unset=True)
    proveedor.sqlmodel_update(update_dict)
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    
    # Invalidate cache
    invalidate_entity_cache("proveedores")
    
    return proveedor


@router.delete(
    "/{id}",
    dependencies=[Depends(get_current_admin_user)]
)
def delete_proveedor(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Delete a proveedor (soft delete).
    """
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    proveedor.estado = False
    session.add(proveedor)
    session.commit()
    
    # Invalidate cache
    invalidate_entity_cache("proveedores")
    
    return Message(message="Proveedor deleted successfully")

