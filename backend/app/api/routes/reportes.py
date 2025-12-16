from typing import Any, Optional

from datetime import date
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from sqlmodel import Session, select, or_, func

from app.api.deps import CurrentUser, SessionDep, get_current_admin_user, get_user_scope
from app.services.report_service import report_service
from app.models import Proveedor, Lote, User, Rol, Sucursal, Bodega, Producto, MovimientoInventario


router = APIRouter(prefix="/reportes", tags=["reportes"])
def _guess_logo_path() -> str | None:
    """Best-effort to locate the logo image in the workspace.
    Tries common paths: frontend/public/assets/images/logo.png
    Returns None if not found.
    """
    import os
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "frontend", "public", "assets", "images", "logo.png"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "email-templates", "build", "reports", "logo.png"),
    ]
    for p in candidates:
        try:
            if os.path.isfile(p):
                return p
        except Exception:
            continue
    return None


def _attachment_response(binary: bytes, filename: str, content_type: str) -> Response:
    # Enviar binarios con longitud definida y cabeceras correctas.
    # Algunos navegadores/visores PDF fallan si el stream no indica tamaño.
    headers = {
        # RFC 5987 for UTF-8 filenames
        "Content-Disposition": f"attachment; filename={filename}; filename*=UTF-8''{filename}",
        "Content-Length": str(len(binary)),
        "Cache-Control": "no-store",
    }
    return Response(content=binary, media_type=content_type, headers=headers)


@router.get("/proveedores")
def reporte_proveedores(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    formato: str = "pdf",
    q: Optional[str] = Query(default=None, description="Búsqueda por nombre/NIT/email/teléfono"),
    estado: Optional[bool] = Query(default=None, description="Estado del proveedor"),
    desde: Optional[date] = Query(default=None, description="Fecha desde (creación aproximada)"),
    hasta: Optional[date] = Query(default=None, description="Fecha hasta (creación aproximada)"),
    max_registros: int = Query(default=500, ge=1, le=5000),
) -> Any:
    # Nota: El modelo Proveedor no tiene fecha_creacion propia.
    # Aproximamos "fecha de creación" como el primer registro de lote asociado.
    # Si no tiene lotes, quedará vacío. Iteración posterior puede agregar columna dedicada.

    # Base query con agregación de fecha mínima de Lote
    stmt = (
        select(
            Proveedor.nombre,
            Proveedor.nit,
            Proveedor.telefono,
            Proveedor.email,
            Proveedor.estado,
            func.min(Lote.fecha_registro).label("fecha_creacion"),
        )
        .select_from(Proveedor)
        .join(Lote, Lote.id_proveedor == Proveedor.id_proveedor, isouter=True)
    )

    filters = []
    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                Proveedor.nombre.ilike(like),
                Proveedor.nit.ilike(like),
                Proveedor.email.ilike(like),
                Proveedor.telefono.ilike(like),
            )
        )
    if estado is not None:
        filters.append(Proveedor.estado == estado)
    if filters:
        stmt = stmt.where(*filters)

    stmt = stmt.group_by(
        Proveedor.nombre,
        Proveedor.nit,
        Proveedor.telefono,
        Proveedor.email,
        Proveedor.estado,
    )

    # Rango de fechas sobre la mínima fecha de lote; excluye proveedores sin lotes si se aplican fechas
    having_conditions = []
    min_fecha = func.min(Lote.fecha_registro)
    if desde is not None:
        having_conditions.append(min_fecha >= desde)
    if hasta is not None:
        having_conditions.append(min_fecha <= hasta)
    if having_conditions:
        from sqlalchemy import and_ as sa_and

        stmt = stmt.having(sa_and(*having_conditions))

    stmt = stmt.limit(max_registros)
    rows = session.exec(stmt).all()

    if formato == "pdf":
        columns = ["Nombre", "NIT", "Contacto", "Estado", "Fecha de creación"]
        printable_rows = []
        for nombre, nit, telefono, email, estado_val, fec in rows:
            contacto = telefono or email or "--"
            estado_txt = "Activo" if estado_val else "Inactivo"
            fec_txt = fec.strftime("%Y-%m-%d") if fec else ""
            printable_rows.append([nombre, nit, contacto, estado_txt, fec_txt])

        filters_meta = {
            "q": q,
            "estado": None if estado is None else ("activo" if estado else "inactivo"),
            "desde": desde.isoformat() if desde else None,
            "hasta": hasta.isoformat() if hasta else None,
            "max_registros": max_registros,
        }

        binary = report_service.render_pdf_table(
            title="Reporte de Proveedores",
            filters=filters_meta,
            columns=columns,
            rows=printable_rows,
            accent_hex="#2D3748",
            logo_path=_guess_logo_path(),
        )
        return _attachment_response(binary, "proveedores.pdf", "application/pdf")
    raise HTTPException(status_code=400, detail="Formato no soportado para proveedores")


@router.get("/usuarios")
def reporte_usuarios(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    formato: str = "pdf",
    id_rol: Optional[int] = Query(default=None, description="Filtrar por rol"),
    id_sucursal: Optional[int] = Query(default=None, description="Filtrar por sucursal"),
    estado: Optional[bool] = Query(default=None, description="Filtrar por estado activo"),
    desde: Optional[date] = Query(default=None, description="Fecha de alta desde"),
    hasta: Optional[date] = Query(default=None, description="Fecha de alta hasta"),
    max_registros: int = Query(default=500, ge=1, le=5000),
) -> Any:
    # Solo admin/superuser
    get_current_admin_user(current_user)
    # Query base con joins a rol y sucursal
    stmt = (
        select(
            User.full_name,
            User.email,
            User.is_active,
            User.fecha_creacion,
            User.id_sucursal,
            User.id_rol,
            Rol.nombre_rol,
            Sucursal.nombre.label("sucursal_nombre"),
        )
        .select_from(User)
        .join(Rol, Rol.id_rol == User.id_rol, isouter=True)
        .join(Sucursal, Sucursal.id_sucursal == User.id_sucursal, isouter=True)
    )

    filters = []
    if id_rol is not None:
        filters.append(User.id_rol == id_rol)
    if id_sucursal is not None:
        filters.append(User.id_sucursal == id_sucursal)
    if estado is not None:
        filters.append(User.is_active == estado)
    # Rango de fechas por fecha de alta (User.fecha_creacion)
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(status_code=400, detail="Rango de fechas inválido: 'desde' > 'hasta'")
    if desde is not None:
        filters.append(User.fecha_creacion >= desde)
    if hasta is not None:
        filters.append(User.fecha_creacion <= hasta)

    if filters:
        stmt = stmt.where(*filters)

    stmt = stmt.limit(max_registros)
    rows = session.exec(stmt).all()

    # Prefetch bodegas por sucursal de los usuarios devueltos
    suc_ids = {r.id_sucursal for r in rows if r.id_sucursal is not None}
    bodega_map: dict[int, list[str]] = {}
    if suc_ids:
        b_stmt = select(Bodega.nombre, Bodega.id_sucursal).where(Bodega.id_sucursal.in_(suc_ids))
        for nombre, suc in session.exec(b_stmt).all():
            bodega_map.setdefault(int(suc), []).append(nombre)

    if formato == "pdf":
        columns = [
            "Nombre",
            "Email",
            "Rol",
            "Sucursal",
            "Bodegas asociadas",
            "Estado",
            "Fecha de alta",
        ]

        printable_rows = []
        for full_name, email, is_active, fecha_creacion, id_suc, id_rol_val, rol_nombre, sucursal_nombre in rows:
            bodegas = bodega_map.get(int(id_suc)) if id_suc is not None else []
            bodegas_str = ", ".join(bodegas or [])
            # Limitar longitud para evitar desbordes; mostrar resumen si es largo
            if len(bodegas_str) > 120:
                bodegas_str = bodegas_str[:117] + "…"
            estado_txt = "Activo" if is_active else "Inactivo"
            fecha_txt = fecha_creacion.strftime("%Y-%m-%d") if fecha_creacion else ""
            printable_rows.append([
                full_name or "--",
                email,
                rol_nombre or ("Rol " + str(id_rol_val) if id_rol_val else "--"),
                sucursal_nombre or ("Sucursal " + str(id_suc) if id_suc else "--"),
                bodegas_str,
                estado_txt,
                fecha_txt,
            ])

        filters_meta = {
            "id_rol": id_rol,
            "id_sucursal": id_sucursal,
            "estado": None if estado is None else ("activo" if estado else "inactivo"),
            "desde": desde.isoformat() if desde else None,
            "hasta": hasta.isoformat() if hasta else None,
            "max_registros": max_registros,
        }

        binary = report_service.render_pdf_table(
            title="Reporte de Usuarios",
            filters=filters_meta,
            columns=columns,
            rows=printable_rows,
            accent_hex="#2D3748",
            logo_path=_guess_logo_path(),
            # Column width profile: Email, Rol, Sucursal moderate; Bodegas wider; Estado and Fecha narrower
            col_widths_fraction=[
                1.2,  # Nombre
                1.6,  # Email
                1.2,  # Rol
                1.2,  # Sucursal
                2.0,  # Bodegas asociadas (wider)
                0.8,  # Estado (narrow)
                1.0,  # Fecha de alta
            ],
        )
        return _attachment_response(binary, "usuarios.pdf", "application/pdf")
    raise HTTPException(status_code=400, detail="Formato no soportado para usuarios")


@router.get("/lotes")
def reporte_lotes(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    formato: str = "pdf",
    desde: Optional[date] = Query(default=None, description="Fecha de recepción desde"),
    hasta: Optional[date] = Query(default=None, description="Fecha de recepción hasta"),
    id_sucursal: Optional[int] = Query(default=None),
    id_bodega: Optional[int] = Query(default=None),
    id_proveedor: Optional[int] = Query(default=None),
    max_registros: int = Query(default=500, ge=1, le=5000),
) -> Any:
    # Alcance: admin ve todo; no admin restringe por sucursal
    scope = get_user_scope(current_user)

    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(status_code=400, detail="Rango de fechas inválido: 'desde' > 'hasta'")

    # Base query para Lotes + joins a Proveedor/Bodega/Sucursal
    stmt = (
        select(
            Lote.id_lote,
            Lote.numero_lote,
            Lote.fecha_vencimiento,
            Lote.fecha_fabricacion,
            Lote.fecha_registro,
            Proveedor.nombre.label("proveedor_nombre"),
            Bodega.nombre.label("bodega_nombre"),
            Sucursal.nombre.label("sucursal_nombre"),
            Bodega.id_sucursal,
        )
        .select_from(Lote)
        .join(Proveedor, Proveedor.id_proveedor == Lote.id_proveedor, isouter=True)
        .join(Bodega, Bodega.id_bodega == Lote.id_bodega, isouter=True)
        .join(Sucursal, Sucursal.id_sucursal == Bodega.id_sucursal, isouter=True)
    )

    filters = []
    if desde is not None:
        filters.append(Lote.fecha_registro >= desde)
    if hasta is not None:
        # incluir el final del día
        from datetime import datetime, time
        filters.append(Lote.fecha_registro <= datetime.combine(hasta, time(23, 59, 59)))
    if id_sucursal is not None:
        filters.append(Bodega.id_sucursal == id_sucursal)
    if id_bodega is not None:
        filters.append(Lote.id_bodega == id_bodega)
    if id_proveedor is not None:
        filters.append(Lote.id_proveedor == id_proveedor)

    # Restringir por scope si no admin
    if scope and scope.get("id_sucursal") and id_sucursal is None:
        filters.append(Bodega.id_sucursal == scope["id_sucursal"])  # type: ignore[index]

    if filters:
        stmt = stmt.where(*filters)

    stmt = stmt.order_by(Lote.fecha_registro.desc()).limit(max_registros)
    base_rows = session.exec(stmt).all()

    # Mapear productos por lote
    lote_ids = [r.id_lote for r in base_rows]
    productos_map: dict[int, list[str]] = {}
    if lote_ids:
        p_stmt = select(Producto.nombre_comercial, Producto.cantidad_total, Producto.id_lote).where(
            Producto.id_lote.in_(lote_ids)
        )
        for nombre, cant, id_lote in session.exec(p_stmt).all():
            # Ser resilientes ante datos antiguos sin id_lote
            if id_lote is None:
                continue
            try:
                lid = int(id_lote)
            except Exception:
                continue
            productos_map.setdefault(lid, []).append(f"{nombre} x{cant}")

    # Receptor (quién recibió) y fecha/hora exacta de recepción (mínima de movimientos de entrada)
    from collections import defaultdict

    recep_user_map: dict[int, str] = {}
    recep_dt_map: dict[int, Any] = {}
    for lote_id in lote_ids:
        # Productos de este lote
        pids_stmt = select(Producto.id_producto).where(Producto.id_lote == lote_id)
        # SQLModel devuelve lista de enteros cuando se selecciona una sola columna
        prod_ids = list(session.exec(pids_stmt).all())
        if not prod_ids:
            continue
        m_stmt = (
            select(MovimientoInventario.fecha_movimiento, User.full_name, User.email)
            .where(MovimientoInventario.id_producto.in_(prod_ids))
            .where(MovimientoInventario.tipo_movimiento == "Entrada")
            .join(User, User.id == MovimientoInventario.id_usuario)
            .order_by(MovimientoInventario.fecha_movimiento.asc())
            .limit(1)
        )
        first = session.exec(m_stmt).first()
        if first:
            fecha_mov, full_name, email = first
            recep_dt_map[lote_id] = fecha_mov
            recep_user_map[lote_id] = full_name or email or "--"
        else:
            # No hay movimientos de entrada registrados
            recep_user_map[lote_id] = "--"

    # Preparar filas para salida
    columns = [
        "Número de lote",
        "Productos del lote",
        "Recibido por",
        "Sucursal",
        "Bodega",
        "Fecha de vencimiento",
        "Fecha de fabricación",
        "Proveedor",
        "Fecha y hora de recepción",
    ]
    printable_rows: list[list[Any]] = []
    for r in base_rows:
        # Manejar posibles nulos defensivamente
        try:
            rid = int(r.id_lote) if r.id_lote is not None else None
        except Exception:
            rid = None
        productos_txt = "; ".join(productos_map.get(rid, [])) if rid is not None else ""
        if rid is not None:
            recibido_por = recep_user_map.get(rid, "--")
            fecha_recep = recep_dt_map.get(rid, r.fecha_registro)
        else:
            recibido_por = "--"
            fecha_recep = r.fecha_registro
        printable_rows.append([
            r.numero_lote,
            productos_txt,
            recibido_por,
            r.sucursal_nombre or "--",
            r.bodega_nombre or "--",
            r.fecha_vencimiento,
            r.fecha_fabricacion,
            r.proveedor_nombre or "--",
            fecha_recep,
        ])

    filters_meta = {
        "desde": desde.isoformat() if desde else None,
        "hasta": hasta.isoformat() if hasta else None,
        "id_sucursal": id_sucursal,
        "id_bodega": id_bodega,
        "id_proveedor": id_proveedor,
        "max_registros": max_registros,
    }

    if formato == "pdf":
        binary = report_service.render_pdf_table(
            title="Reporte de Lotes",
            filters=filters_meta,
            columns=columns,
            rows=printable_rows,
            accent_hex="#0EA5A2",
            logo_path=_guess_logo_path(),
            landscape_mode=True,
            # Make product and reception columns wider; Estado not present here
            col_widths_fraction=[
                1.2,  # Número de lote
                2.2,  # Productos del lote (wider)
                1.2,  # Recibido por
                1.0,  # Sucursal
                1.0,  # Bodega
                1.0,  # Fecha de vencimiento
                1.0,  # Fecha de fabricación
                1.0,  # Proveedor
                1.4,  # Fecha y hora de recepción (wider)
            ],
        )
        return _attachment_response(binary, "lotes.pdf", "application/pdf")
    if formato == "excel":
        binary = report_service.render_excel_xlsx(
            sheet="Lotes",
            headers=columns,
            rows=printable_rows,
            date_columns=[5, 6],
            datetime_columns=[8],
        )
        return _attachment_response(
            binary,
            "lotes.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    raise HTTPException(status_code=400, detail="Formato no soportado para lotes")
