from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Lote, LoteCreate, LotePublic, LotesPublic, LoteUpdate, Message

router = APIRouter(prefix="/lotes", tags=["lotes"])


@router.get("/", response_model=LotesPublic)
def read_lotes(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve lotes.
    """
    count_statement = select(func.count()).select_from(Lote)
    count = session.exec(count_statement).one()
    statement = select(Lote).offset(skip).limit(limit)
    lotes = session.exec(statement).all()
    return LotesPublic(data=lotes, count=count)


@router.get("/{id}", response_model=LotePublic)
def read_lote(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get lote by ID.
    """
    lote = session.get(Lote, id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote not found")
    return lote


@router.post("/", response_model=LotePublic)
def create_lote(
    *, session: SessionDep, current_user: CurrentUser, lote_in: LoteCreate
) -> Any:
    """
    Create new lote.
    """
    lote = Lote.model_validate(lote_in)
    session.add(lote)
    session.commit()
    session.refresh(lote)
    return lote


@router.put("/{id}", response_model=LotePublic)
def update_lote(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    lote_in: LoteUpdate,
) -> Any:
    """
    Update a lote.
    """
    lote = session.get(Lote, id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote not found")
    update_dict = lote_in.model_dump(exclude_unset=True)
    lote.sqlmodel_update(update_dict)
    session.add(lote)
    session.commit()
    session.refresh(lote)
    return lote

