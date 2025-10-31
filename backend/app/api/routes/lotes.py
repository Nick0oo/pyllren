from typing import Any
from datetime import date, datetime
from pydantic import field_validator, model_validator
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select
from sqlalchemy import or_

from app.api.deps import CurrentUser, SessionDep, get_user_scope, ensure_bodega_in_scope, is_admin_user
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key
)
from app.models import (
    Lote,
    LoteCreate,
    LotePublic,
    LotesPublic,
    LoteUpdate,
    Message,
    Bodega,
    Producto,
    ProductoCreate,
    MovimientoInventario,
    Auditoria,
)
from sqlmodel import col
from sqlmodel import SQLModel, Field


class RecepcionProductoItem(SQLModel):
    nombre_comercial: str
    nombre_generico: str | None = Field(default=None)
    codigo_interno: str | None = Field(default=None)
    codigo_barras: str | None = Field(default=None)
    forma_farmaceutica: str
    concentracion: str
    presentacion: str
    unidad_medida: str
    cantidad: int = Field(gt=0)
    stock_minimo: int
    stock_maximo: int

    @field_validator("nombre_generico", "codigo_interno", "codigo_barras", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> str | None:
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed == "":
                return None
            return v_trimmed
        return v


class RecepcionLotePayload(SQLModel):
    lote: LoteCreate
    items: list[RecepcionProductoItem]

router = APIRouter(prefix="/lotes", tags=["lotes"])


@router.get("/", response_model=LotesPublic)
def read_lotes(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    id_bodega: int | None = None,
    id_sucursal: int | None = None,
    id_proveedor: int | None = None,
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
) -> Any:
    """
    Retrieve lotes.
    """
    scope = get_user_scope(current_user)
    # Admin puede fijar id_sucursal; resto se ignora
    sc_id_sucursal = id_sucursal if scope is None else scope.get("id_sucursal")

    # Generate cache key con filtros
    cache_key = list_cache_key(
        "lotes",
        skip=skip,
        limit=limit,
        q=q,
        id_bodega=id_bodega,
        id_sucursal=sc_id_sucursal,
        id_proveedor=id_proveedor,
        fecha_desde=str(fecha_desde) if fecha_desde else None,
        fecha_hasta=str(fecha_hasta) if fecha_hasta else None,
    )
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return LotesPublic(**cached_result)
    
    # Build base query with outerjoin para manejar lotes sin bodega
    base_stmt = select(Lote).outerjoin(Bodega, Bodega.id_bodega == Lote.id_bodega)

    if sc_id_sucursal is not None:
        # Si no es admin, filtrar por sucursal o lotes sin bodega
        base_stmt = base_stmt.where(
            or_(
                Bodega.id_sucursal == sc_id_sucursal,  # type: ignore[attr-defined]
                Lote.id_bodega.is_(None)  # type: ignore[attr-defined]
            )
        )
    if id_bodega is not None:
        base_stmt = base_stmt.where(Lote.id_bodega == id_bodega)
    if id_proveedor is not None:
        base_stmt = base_stmt.where(Lote.id_proveedor == id_proveedor)
    if q:
        base_stmt = base_stmt.where(Lote.numero_lote.contains(q))
    if fecha_desde is not None:
        base_stmt = base_stmt.where(Lote.fecha_registro >= datetime.combine(fecha_desde, datetime.min.time()))
    if fecha_hasta is not None:
        base_stmt = base_stmt.where(Lote.fecha_registro <= datetime.combine(fecha_hasta, datetime.max.time()))

    count = session.exec(select(func.count()).select_from(base_stmt.subquery())).one()
    lotes = session.exec(base_stmt.offset(skip).limit(limit)).all()
    
    result = LotesPublic(data=lotes, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get("/{id}", response_model=LotePublic)
def read_lote(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get lote by ID.
    """
    # Generate cache key
    cache_key = item_cache_key("lotes", id)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return LotePublic(**cached_result)
    
    lote = session.get(Lote, id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote not found")
    # Validar alcance
    if not is_admin_user(current_user):
        bodega = session.get(Bodega, lote.id_bodega)
        if not bodega or bodega.id_sucursal != current_user.id_sucursal:
            raise HTTPException(status_code=404, detail="Lote not found")
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, lote.model_dump(), ttl=300)
    
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
    
    # Invalidate cache
    invalidate_entity_cache("lotes")
    invalidate_entity_cache("proveedores")  # Stats may change
    
    return lote


# -----------------------------------------------------------------------------
# Recepción de lotes con productos
# -----------------------------------------------------------------------------
def generar_numero_lote_unico(session: SessionDep, id_bodega: int | None, id_proveedor: int) -> str:
    """Genera un número de lote único basado en timestamp y contador."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bodega_prefix = f"B{id_bodega}-" if id_bodega else "N-"
    base_numero = f"LOT-{bodega_prefix}{timestamp}"
    
    # Verificar si ya existe, si existe agregar contador
    contador = 1
    numero_lote = base_numero
    while True:
        if id_bodega is None:
            exists = session.exec(
                select(Lote).where(
                    Lote.numero_lote == numero_lote,
                    Lote.id_bodega.is_(None),  # type: ignore[attr-defined]
                )
            ).first()
        else:
            exists = session.exec(
                select(Lote).where(
                    Lote.numero_lote == numero_lote,
                    Lote.id_bodega == id_bodega,
                )
            ).first()
        
        if not exists:
            break
        
        numero_lote = f"{base_numero}-{contador:03d}"
        contador += 1
        if contador > 999:
            # Fallback: usar timestamp más microsegundos
            from time import time
            numero_lote = f"LOT-{bodega_prefix}{int(time() * 1000000)}"
            break
    
    return numero_lote


@router.post("/recepcion")
def recepcion_lote(
    *, session: SessionDep, current_user: CurrentUser, payload: RecepcionLotePayload
) -> Any:
    if not payload.items:
        raise HTTPException(status_code=400, detail="La recepción debe incluir productos")

    # Validaciones de fechas
    if payload.lote.fecha_fabricacion > payload.lote.fecha_vencimiento:
        raise HTTPException(status_code=400, detail="Fecha de fabricación no puede ser mayor a vencimiento")

    # Verificar alcance de bodega si se proporcionó
    if payload.lote.id_bodega is not None:
        ensure_bodega_in_scope(session, payload.lote.id_bodega, current_user)

    # Generar número de lote automático único si no se proporcionó
    # Siempre generamos uno nuevo para asegurar unicidad
    numero_lote = generar_numero_lote_unico(
        session, 
        payload.lote.id_bodega, 
        payload.lote.id_proveedor
    )

    # Crear Lote con número generado automáticamente
    lote_data = payload.lote.model_dump(exclude_none=True)
    lote_data["numero_lote"] = numero_lote
    lote = Lote.model_validate(lote_data)
    session.add(lote)
    session.commit()
    session.refresh(lote)

    productos_ids: list[int] = []

    # Crear productos y movimientos de entrada
    bodega = session.get(Bodega, lote.id_bodega) if lote.id_bodega is not None else None
    for item in payload.items:
        prod = Producto(
            nombre_comercial=item.nombre_comercial,
            nombre_generico=item.nombre_generico,
            codigo_interno=item.codigo_interno,
            codigo_barras=item.codigo_barras,
            forma_farmaceutica=item.forma_farmaceutica,
            concentracion=item.concentracion,
            presentacion=item.presentacion,
            unidad_medida=item.unidad_medida,
            cantidad_total=item.cantidad,
            cantidad_disponible=item.cantidad,
            stock_minimo=item.stock_minimo,
            stock_maximo=item.stock_maximo,
            id_lote=lote.id_lote,  # type: ignore[arg-type]
        )
        session.add(prod)
        session.commit()
        session.refresh(prod)
        productos_ids.append(prod.id_producto)  # type: ignore[attr-defined]

        movimiento = MovimientoInventario(
            tipo_movimiento="Entrada",
            cantidad=item.cantidad,
            descripcion=f"Recepción lote {lote.numero_lote}",
            id_producto=prod.id_producto,  # type: ignore[arg-type]
            id_usuario=current_user.id,  # type: ignore[arg-type]
            id_sucursal_origen=None,
            id_sucursal_destino=bodega.id_sucursal if bodega else None,
        )
        session.add(movimiento)
        session.commit()

    # Auditoría
    audit = Auditoria(
        entidad_afectada="lote",
        id_registro_afectado=str(lote.id_lote),  # type: ignore[arg-type]
        accion="recepcion_lote_creado",
        detalle={
            "lote": lote.model_dump(mode="json"),
            "productos_ids": productos_ids,
        },
        resultado="Éxito",
        id_usuario=current_user.id,  # type: ignore[arg-type]
    )
    session.add(audit)
    session.commit()

    # Invalidate caches
    invalidate_entity_cache("lotes")
    invalidate_entity_cache("productos")

    return {"lote": lote, "productos_ids": productos_ids}


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
    
    # Invalidate cache
    invalidate_entity_cache("lotes")
    invalidate_entity_cache("proveedores")  # Stats may change
    
    return lote

