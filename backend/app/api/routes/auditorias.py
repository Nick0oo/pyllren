from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Auditoria,
    AuditoriaCreate,
    AuditoriaPublic,
    AuditoriasPublic,
)

router = APIRouter(prefix="/auditorias", tags=["auditorias"])


@router.get("/", response_model=AuditoriasPublic)
def read_auditorias(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve auditorias.
    """
    count_statement = select(func.count()).select_from(Auditoria)
    count = session.exec(count_statement).one()
    statement = select(Auditoria).offset(skip).limit(limit)
    auditorias = session.exec(statement).all()
    return AuditoriasPublic(data=auditorias, count=count)


@router.get("/{id}", response_model=AuditoriaPublic)
def read_auditoria(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get auditoria by ID.
    """
    auditoria = session.get(Auditoria, id)
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoria not found")
    return auditoria


@router.post("/", response_model=AuditoriaPublic)
def create_auditoria(
    *, session: SessionDep, current_user: CurrentUser, auditoria_in: AuditoriaCreate
) -> Any:
    """
    Create new auditoria record.
    """
    auditoria = Auditoria.model_validate(auditoria_in)
    session.add(auditoria)
    session.commit()
    session.refresh(auditoria)
    return auditoria

