from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
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
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve productos.
    """
    count_statement = select(func.count()).select_from(Producto)
    count = session.exec(count_statement).one()
    statement = select(Producto).offset(skip).limit(limit)
    productos = session.exec(statement).all()
    return ProductosPublic(data=productos, count=count)


@router.get("/{id}", response_model=ProductoPublic)
def read_producto(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get producto by ID.
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
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
    return Message(message="Producto deleted successfully")

