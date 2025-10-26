from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key
)
from app.models import (
    Bodega,
    BodegaCreate,
    BodegaPublic,
    BodegasPublic,
    BodegaUpdate,
    Message,
)

router = APIRouter(prefix="/bodegas", tags=["bodegas"])


@router.get("/", response_model=BodegasPublic)
def read_bodegas(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve bodegas.
    """
    # Generate cache key
    cache_key = list_cache_key("bodegas", skip=skip, limit=limit)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return BodegasPublic(**cached_result)
    
    count_statement = select(func.count()).select_from(Bodega)
    count = session.exec(count_statement).one()
    statement = select(Bodega).offset(skip).limit(limit)
    bodegas = session.exec(statement).all()
    
    result = BodegasPublic(data=bodegas, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get("/{id}", response_model=BodegaPublic)
def read_bodega(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get bodega by ID.
    """
    # Generate cache key
    cache_key = item_cache_key("bodegas", id)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return BodegaPublic(**cached_result)
    
    bodega = session.get(Bodega, id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, bodega.model_dump(), ttl=300)
    
    return bodega


@router.post("/", response_model=BodegaPublic)
def create_bodega(
    *, session: SessionDep, current_user: CurrentUser, bodega_in: BodegaCreate
) -> Any:
    """
    Create new bodega.
    """
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
    """
    bodega = session.get(Bodega, id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")
    update_dict = bodega_in.model_dump(exclude_unset=True)
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
    """
    bodega = session.get(Bodega, id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")
    bodega.estado = False
    session.add(bodega)
    session.commit()
    
    # Invalidate cache
    invalidate_entity_cache("bodegas")
    
    return Message(message="Bodega deleted successfully")

