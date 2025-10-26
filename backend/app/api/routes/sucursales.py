from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Sucursal,
    SucursalCreate,
    SucursalPublic,
    SucursalesPublic,
    SucursalUpdate,
)

router = APIRouter(prefix="/sucursales", tags=["sucursales"])


@router.get("/", response_model=SucursalesPublic)
def read_sucursales(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve sucursales.
    """
    count_statement = select(func.count()).select_from(Sucursal)
    count = session.exec(count_statement).one()
    statement = select(Sucursal).offset(skip).limit(limit)
    sucursales = session.exec(statement).all()
    return SucursalesPublic(data=sucursales, count=count)


@router.get("/{id}", response_model=SucursalPublic)
def read_sucursal(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get sucursal by ID.
    """
    sucursal = session.get(Sucursal, id)
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal not found")
    return sucursal


@router.post("/", response_model=SucursalPublic)
def create_sucursal(
    *, session: SessionDep, current_user: CurrentUser, sucursal_in: SucursalCreate
) -> Any:
    """
    Create new sucursal.
    """
    sucursal = Sucursal.model_validate(sucursal_in)
    session.add(sucursal)
    session.commit()
    session.refresh(sucursal)
    return sucursal


@router.put("/{id}", response_model=SucursalPublic)
def update_sucursal(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    sucursal_in: SucursalUpdate,
) -> Any:
    """
    Update a sucursal.
    """
    sucursal = session.get(Sucursal, id)
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal not found")
    update_dict = sucursal_in.model_dump(exclude_unset=True)
    sucursal.sqlmodel_update(update_dict)
    session.add(sucursal)
    session.commit()
    session.refresh(sucursal)
    return sucursal


@router.delete("/{id}")
def delete_sucursal(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Delete a sucursal (soft delete).
    """
    sucursal = session.get(Sucursal, id)
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal not found")
    sucursal.estado = False
    session.add(sucursal)
    session.commit()
    return Message(message="Sucursal deleted successfully")

