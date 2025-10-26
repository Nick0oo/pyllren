from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    MovimientoInventario,
    MovimientoInventarioCreate,
    MovimientoInventarioPublic,
    MovimientosInventarioPublic,
    MovimientoInventarioUpdate,
)

router = APIRouter(prefix="/movimientos", tags=["movimientos"])


@router.get("/", response_model=MovimientosInventarioPublic)
def read_movimientos(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve movimientos de inventario.
    """
    count_statement = select(func.count()).select_from(MovimientoInventario)
    count = session.exec(count_statement).one()
    statement = select(MovimientoInventario).offset(skip).limit(limit)
    movimientos = session.exec(statement).all()
    return MovimientosInventarioPublic(data=movimientos, count=count)


@router.get("/{id}", response_model=MovimientoInventarioPublic)
def read_movimiento(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get movimiento by ID.
    """
    movimiento = session.get(MovimientoInventario, id)
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento not found")
    return movimiento


@router.post("/", response_model=MovimientoInventarioPublic)
def create_movimiento(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    movimiento_in: MovimientoInventarioCreate,
) -> Any:
    """
    Create new movimiento de inventario.
    """
    movimiento = MovimientoInventario.model_validate(movimiento_in)
    session.add(movimiento)
    session.commit()
    session.refresh(movimiento)
    return movimiento


@router.put("/{id}", response_model=MovimientoInventarioPublic)
def update_movimiento(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    movimiento_in: MovimientoInventarioUpdate,
) -> Any:
    """
    Update a movimiento.
    """
    movimiento = session.get(MovimientoInventario, id)
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento not found")
    update_dict = movimiento_in.model_dump(exclude_unset=True)
    movimiento.sqlmodel_update(update_dict)
    session.add(movimiento)
    session.commit()
    session.refresh(movimiento)
    return movimiento

