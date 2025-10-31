from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key
)
from app.models import (
    Message,
    Producto,
    ProductoCreate,
    ProductoPublic,
    ProductosPublic,
    ProductoUpdate,
)

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("/", response_model=ProductosPublic)
def read_productos(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
) -> Any:
    """
    Retrieve productos.
    """
    # Generate cache key
    cache_key = list_cache_key("productos", skip=skip, limit=limit, q=q)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return ProductosPublic(**cached_result)
    
    stmt = select(Producto)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Producto.nombre_comercial.ilike(like))
            | (Producto.nombre_generico.ilike(like))
            | (Producto.codigo_interno.ilike(like))
            | (Producto.codigo_barras.ilike(like))
        )
    count = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    statement = stmt.offset(skip).limit(limit)
    productos = session.exec(statement).all()
    
    result = ProductosPublic(data=productos, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get("/{id}", response_model=ProductoPublic)
def read_producto(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get producto by ID.
    """
    # Generate cache key
    cache_key = item_cache_key("productos", id)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return ProductoPublic(**cached_result)
    
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, producto.model_dump(), ttl=300)
    
    return producto


@router.post("/", response_model=ProductoPublic)
def create_producto(
    *, session: SessionDep, current_user: CurrentUser, producto_in: ProductoCreate
) -> Any:
    """
    Create new producto.
    """
    producto = Producto.model_validate(producto_in)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    
    # Invalidate cache
    invalidate_entity_cache("productos")
    
    return producto


@router.put("/{id}", response_model=ProductoPublic)
def update_producto(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    producto_in: ProductoUpdate,
) -> Any:
    """
    Update a producto.
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    update_dict = producto_in.model_dump(exclude_unset=True)
    producto.sqlmodel_update(update_dict)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    
    # Invalidate cache
    invalidate_entity_cache("productos")
    
    return producto


@router.delete("/{id}")
def delete_producto(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Delete a producto (soft delete).
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    producto.estado = False
    session.add(producto)
    session.commit()
    
    # Invalidate cache
    invalidate_entity_cache("productos")
    
    return Message(message="Producto deleted successfully")

