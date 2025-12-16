import uuid
from typing import Any

from sqlmodel import Session

from app.core.websocket_manager import manager
from app import crud


async def emit_notification(
    *,
    session: Session,
    tipo: str,
    receptor_id: uuid.UUID,
    payload: dict[str, Any],
    prioridad: str = "normal",
    sucursal_id: int | None = None,
    bodega_id: int | None = None,
    meta_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persiste y envía en vivo una notificación al usuario si está conectado."""
    db_obj = crud.create_notification(
        session=session,
        tipo=tipo,
        receptor_id=receptor_id,
        payload=payload,
        prioridad=prioridad,
        sucursal_id=sucursal_id,
        bodega_id=bodega_id,
        meta_data=meta_data,
    )

    message = {
        "type": tipo,
        "notification_id": db_obj.id,
        "payload": payload,
        "created_at": db_obj.creado_en.isoformat(),
        "priority": prioridad,
    }

    if manager.is_connected(receptor_id):
        await manager.send_to_user(receptor_id, message)

    return message
