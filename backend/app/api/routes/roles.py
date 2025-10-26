from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key
)
from app.models import Rol, RolCreate, RolPublic, RolesPublic, RolUpdate

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=RolesPublic)
def read_roles(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve roles.
    """
    # Generate cache key
    cache_key = list_cache_key("roles", skip=skip, limit=limit)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return RolesPublic(**cached_result)
    
    count_statement = select(func.count()).select_from(Rol)
    count = session.exec(count_statement).one()
    statement = select(Rol).offset(skip).limit(limit)
    roles = session.exec(statement).all()
    
    result = RolesPublic(data=roles, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get("/{id}", response_model=RolPublic)
def read_rol(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get rol by ID.
    """
    # Generate cache key
    cache_key = item_cache_key("roles", id)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return RolPublic(**cached_result)
    
    rol = session.get(Rol, id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol not found")
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, rol.model_dump(), ttl=300)
    
    return rol


@router.post("/", response_model=RolPublic)
def create_rol(
    *, session: SessionDep, current_user: CurrentUser, rol_in: RolCreate
) -> Any:
    """
    Create new rol.
    """
    rol = Rol.model_validate(rol_in)
    session.add(rol)
    session.commit()
    session.refresh(rol)
    
    # Invalidate cache
    invalidate_entity_cache("roles")
    
    return rol


@router.put("/{id}", response_model=RolPublic)
def update_rol(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    rol_in: RolUpdate,
) -> Any:
    """
    Update a rol.
    """
    rol = session.get(Rol, id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol not found")
    update_dict = rol_in.model_dump(exclude_unset=True)
    rol.sqlmodel_update(update_dict)
    session.add(rol)
    session.commit()
    session.refresh(rol)
    
    # Invalidate cache
    invalidate_entity_cache("roles")
    
    return rol

