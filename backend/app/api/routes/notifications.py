from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, get_current_user
from app import crud
from app.models import NotificacionesPublic, NotificacionPublic

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificacionesPublic)
def list_notifications(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    leida: bool | None = None,
    tipo: str | None = None,
) -> Any:
    notifications, count = crud.get_notifications(
        session=session,
        receptor_id=current_user.id,
        leida=leida,
        tipo=tipo,
        skip=skip,
        limit=limit,
    )
    return NotificacionesPublic(data=notifications, count=count)


@router.patch("/{notification_id}/read", response_model=NotificacionPublic)
def mark_read(
    notification_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    notification = crud.mark_notification_as_read(
        session=session,
        notification_id=notification_id,
        receptor_id=current_user.id,
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.get("/unread/count")
def unread_count(session: SessionDep, current_user: CurrentUser) -> dict[str, int]:
    count = crud.count_unread_notifications(session=session, receptor_id=current_user.id)
    return {"count": count}


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, session: SessionDep, current_user: CurrentUser) -> dict[str, bool]:
    ok = crud.delete_notification(session=session, notification_id=notification_id, receptor_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"deleted": True}
