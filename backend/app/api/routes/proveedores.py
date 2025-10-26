from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Proveedor,
    ProveedorCreate,
    ProveedorPublic,
    ProveedoresPublic,
    ProveedorUpdate,
)

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.get("/", response_model=ProveedoresPublic)
def read_proveedores(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve proveedores.
    """
    count_statement = select(func.count()).select_from(Proveedor)
    count = session.exec(count_statement).one()
    statement = select(Proveedor).offset(skip).limit(limit)
    proveedores = session.exec(statement).all()
    return ProveedoresPublic(data=proveedores, count=count)


@router.get("/{id}", response_model=ProveedorPublic)
def read_proveedor(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get proveedor by ID.
    """
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    return proveedor


@router.post("/", response_model=ProveedorPublic)
def create_proveedor(
    *, session: SessionDep, current_user: CurrentUser, proveedor_in: ProveedorCreate
) -> Any:
    """
    Create new proveedor.
    """
    proveedor = Proveedor.model_validate(proveedor_in)
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor


@router.put("/{id}", response_model=ProveedorPublic)
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
    update_dict = proveedor_in.model_dump(exclude_unset=True)
    proveedor.sqlmodel_update(update_dict)
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor


@router.delete("/{id}")
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
    return Message(message="Proveedor deleted successfully")

