import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session

from app import crud
from app.api.deps import CurrentUser, SessionDep, ensure_bodega_in_scope, is_admin_user
from app.models import (
    Bodega,
    Transferencia,
    TransferenciaCreate,
    TransferenciaPublic,
)
import app.models as models
from app.services.notification_service import emit_notification

router = APIRouter(prefix="/transferencias", tags=["transferencias"])


def _get_bodega_or_404(session: Session, bodega_id: int) -> Bodega:
    bodega = session.get(Bodega, bodega_id)
    if not bodega:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bodega not found")
    return bodega


@router.post("/", response_model=TransferenciaPublic, status_code=status.HTTP_201_CREATED)
async def crear_transferencia(
    *, session: SessionDep, current_user: CurrentUser, transferencia_in: TransferenciaCreate
) -> Any:
    # Permisos: Farmacéutico (id_rol=2), Administrador (id_rol=1) o Superusuario pueden crear transferencias
    if not (
        getattr(current_user, "is_superuser", False)
        or getattr(current_user, "id_rol", None) in (1, 2)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Administrador, Farmacéutico o Superusuario pueden crear transferencias",
        )

    # Validar alcance en bodega origen
    ensure_bodega_in_scope(session, transferencia_in.id_bodega_origen, current_user)

    bodega_origen = _get_bodega_or_404(session, transferencia_in.id_bodega_origen)
    bodega_destino = _get_bodega_or_404(session, transferencia_in.id_bodega_destino)

    transferencia = Transferencia.model_validate(
        transferencia_in,
        update={
            "id_usuario_origen": current_user.id,
            "estado": "pendiente",
            "fecha_creacion": datetime.now(),
            "fecha_actualizacion": datetime.now(),
        },
    )
    session.add(transferencia)
    session.commit()
    session.refresh(transferencia)

    # Aviso informativo a usuarios de la sucursal destino (sin acciones)
    usuarios_destino = crud.get_users_by_sucursal(session=session, sucursal_id=bodega_destino.id_sucursal)
    usuarios_destino_ids = [u.id for u in usuarios_destino if not is_admin_user(u) and u.id != current_user.id]

    # Intentar usar nombre del usuario si está disponible (para ambos payloads)
    usuario_nombre = getattr(current_user, "nombre", None) or getattr(current_user, "full_name", None) or current_user.email

    user_payload = {
        "transferencia_id": transferencia.id_transferencia,
        "origen": bodega_origen.nombre,
        "destino": bodega_destino.nombre,
        "productos": transferencia.productos,
        "usuario_origen": str(current_user.id),
        "usuario_origen_nombre": usuario_nombre,
    }

    for receptor_id in usuarios_destino_ids:
        await emit_notification(
            session=session,
            tipo="transferencia:info_destino",
            receptor_id=receptor_id,
            payload=user_payload,
            prioridad="baja",
            sucursal_id=bodega_destino.id_sucursal,
            bodega_id=bodega_destino.id_bodega,
            meta_data={"transferencia_id": transferencia.id_transferencia},
        )

    # Notificar principalmente a administradores con acción; excluir al emisor si también es admin

    # Notificación para administradores (rol o superuser)
    admin_users = crud.get_admin_users(session=session)
    admin_receptor_ids = [u.id for u in admin_users if u.id != current_user.id]

    # usuario_nombre ya calculado arriba
    # Enriquecer con numero_lote si viene id_lote en productos
    lotes_detalle: list[dict[str, Any]] = []
    try:
        for p in (transferencia.productos or []):
            if p and isinstance(p, dict) and p.get("id_lote"):
                lid = p.get("id_lote")
                lote = session.get(models.Lote, lid)
                if lote:
                    lotes_detalle.append({"id_lote": lid, "numero_lote": lote.numero_lote})
    except Exception:
        pass

    admin_payload = {
        "transferencia_id": transferencia.id_transferencia,
        "origen": bodega_origen.nombre,
        "destino": bodega_destino.nombre,
        "productos": transferencia.productos,
        "lotes": lotes_detalle,
        "usuario_origen": str(current_user.id),
        "usuario_origen_nombre": usuario_nombre,
        "mensaje": f"{usuario_nombre} ha transferido el lote {lotes_detalle[0]['numero_lote'] if lotes_detalle else ''} de la bodega {bodega_origen.nombre} a la bodega {bodega_destino.nombre}",
    }

    for admin_id in admin_receptor_ids:
        await emit_notification(
            session=session,
            tipo="transferencia:admin",
            receptor_id=admin_id,
            payload=admin_payload,
            prioridad="alta",
            sucursal_id=bodega_destino.id_sucursal,
            bodega_id=bodega_destino.id_bodega,
            meta_data={"transferencia_id": transferencia.id_transferencia},
        )

    return transferencia


@router.patch("/{transferencia_id}/confirmar", response_model=TransferenciaPublic)
async def confirmar_transferencia(
    transferencia_id: int, *, session: SessionDep, current_user: CurrentUser
) -> Any:
    transferencia = session.get(Transferencia, transferencia_id)
    if not transferencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transferencia not found")

    # Solo administradores pueden confirmar o cancelar
    if not is_admin_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden confirmar transferencias")

    if transferencia.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transferencia no está pendiente")

    transferencia.estado = "confirmada"
    transferencia.fecha_actualizacion = datetime.now()
    session.add(transferencia)
    session.commit()
    session.refresh(transferencia)

    # Actualizar inventario y ubicación de lotes/productos en confirmación
    # Se espera que transferencia.productos sea una lista de objetos con al menos
    # { id_producto?: int, cantidad?: int, id_lote?: int }
    # Regla simple: si viene id_producto y cantidad, ajustamos stock (resta en origen, suma en destino)
    # Si viene id_lote y no hay id_producto, movemos el lote completo a la bodega destino
    try:
        productos = transferencia.productos or []
        for item in productos:
            # Ajuste por producto específico
            prod_id = item.get("id_producto")
            cantidad = item.get("cantidad")
            if prod_id and isinstance(cantidad, int) and cantidad > 0:
                # Resta en origen (salida)
                crud.ajustar_stock_producto(session=session, producto_id=prod_id, cantidad=cantidad, es_suma=False)
                # Suma en destino (entrada)
                crud.ajustar_stock_producto(session=session, producto_id=prod_id, cantidad=cantidad, es_suma=True)

            # Movimiento por lote completo
            lote_id = item.get("id_lote")
            if lote_id and not prod_id:
                lote = session.get(models.Lote, lote_id)
                if lote:
                    lote.id_bodega = transferencia.id_bodega_destino
                    session.add(lote)

        session.commit()
    except Exception:
        # No romper confirmación por errores de ajuste; se puede auditar posteriormente
        session.rollback()

    bodega_destino = _get_bodega_or_404(session, transferencia.id_bodega_destino)
    bodega_origen = _get_bodega_or_404(session, transferencia.id_bodega_origen)

    payload = {
        "transferencia_id": transferencia.id_transferencia,
        "confirmado_por": str(current_user.id),
        "destino": bodega_destino.nombre,
        "origen": bodega_origen.nombre,
    }

    await emit_notification(
        session=session,
        tipo="transferencia:confirmada",
        receptor_id=transferencia.id_usuario_origen,
        payload=payload,
        prioridad="normal",
        sucursal_id=bodega_origen.id_sucursal,
        bodega_id=bodega_origen.id_bodega,
        meta_data={"transferencia_id": transferencia.id_transferencia},
    )

    # Marcar como leídas todas las notificaciones relacionadas para el admin que actuó
    crud.mark_related_notifications_as_read(
        session=session,
        receptor_id=current_user.id,
        transferencia_id=transferencia.id_transferencia,
    )

    # Notificar a todos los administradores para que actualicen su UI (y oculten la acción)
    admin_users = crud.get_admin_users(session=session)
    for admin in admin_users:
        await emit_notification(
            session=session,
            tipo="transferencia:confirmada",
            receptor_id=admin.id,
            payload=payload,
            prioridad="baja",
            sucursal_id=bodega_destino.id_sucursal,
            bodega_id=bodega_destino.id_bodega,
            meta_data={"transferencia_id": transferencia.id_transferencia},
        )

    return transferencia


@router.patch("/{transferencia_id}/cancelar", response_model=TransferenciaPublic)
async def cancelar_transferencia(
    transferencia_id: int,
    *,
    session: SessionDep,
    current_user: CurrentUser,
    motivo: str | None = None,
) -> Any:
    transferencia = session.get(Transferencia, transferencia_id)
    if not transferencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transferencia not found")

    # Solo administradores pueden confirmar o cancelar
    if not is_admin_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden cancelar transferencias")

    if transferencia.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transferencia no está pendiente")

    transferencia.estado = "cancelada"
    transferencia.fecha_actualizacion = datetime.now()
    session.add(transferencia)
    session.commit()
    session.refresh(transferencia)

    bodega_destino = _get_bodega_or_404(session, transferencia.id_bodega_destino)
    bodega_origen = _get_bodega_or_404(session, transferencia.id_bodega_origen)

    payload = {
        "transferencia_id": transferencia.id_transferencia,
        "cancelado_por": str(current_user.id),
        "razon": motivo or "",
        "destino": bodega_destino.nombre,
        "origen": bodega_origen.nombre,
    }

    await emit_notification(
        session=session,
        tipo="transferencia:cancelada",
        receptor_id=transferencia.id_usuario_origen,
        payload=payload,
        prioridad="normal",
        sucursal_id=bodega_origen.id_sucursal,
        bodega_id=bodega_origen.id_bodega,
        meta_data={"transferencia_id": transferencia.id_transferencia},
    )

    crud.mark_related_notifications_as_read(
        session=session,
        receptor_id=current_user.id,
        transferencia_id=transferencia.id_transferencia,
    )

    # Notificar a administradores para sincronizar la UI remota
    admin_users = crud.get_admin_users(session=session)
    for admin in admin_users:
        await emit_notification(
            session=session,
            tipo="transferencia:cancelada",
            receptor_id=admin.id,
            payload=payload,
            prioridad="baja",
            sucursal_id=bodega_destino.id_sucursal,
            bodega_id=bodega_destino.id_bodega,
            meta_data={"transferencia_id": transferencia.id_transferencia},
        )

    return transferencia
