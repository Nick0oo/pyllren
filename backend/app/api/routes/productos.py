from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import func, select
from sqlalchemy.orm import selectinload
import sys
import traceback
import logging

from app.api.deps import CurrentUser, SessionDep, get_user_scope
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key
)
from app.models import (
    Message,
    Producto,
    ProductoCreate,
    ProductoPublicExtended,
    ProductosPublicExtended,
    ProductoUpdate,
    Lote,
    Bodega,
    ProductosStats,
)

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("/", response_model=ProductosPublicExtended)
def read_productos(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    id_sucursal: int | None = None,
) -> Any:
    """
    Retrieve productos filtered by sucursal scope.
    
    - Admins can specify id_sucursal or see all (None)
    - Non-admins are restricted to their own sucursal
    """
    # Get user scope (None for admin, {"id_sucursal": X} for others)
    scope = get_user_scope(current_user)
    sc_id_sucursal = scope.get("id_sucursal") if scope else id_sucursal
    
    # Generate cache key including scope
    cache_key = list_cache_key("productos", skip=skip, limit=limit, q=q, id_sucursal=sc_id_sucursal)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        # If cached data lacks enrichment (numero_lote / bodega_nombre) try to enrich in batch
        try:
            needs_enrich = any((item.get("numero_lote") is None) for item in cached_result.get("data", []))
        except Exception:
            needs_enrich = False

        if needs_enrich and cached_result.get("data"):
            # Gather id_lote values to enrich
            ids = [it.get("id_lote") for it in cached_result["data"] if it.get("id_lote")]
            if ids:
                lote_stmt = select(Lote).where(Lote.id_lote.in_(ids)).options(selectinload(Lote.bodega))
                lotes = {l.id_lote: l for l in session.exec(lote_stmt).all()}
                for it in cached_result["data"]:
                    lid = it.get("id_lote")
                    lote = lotes.get(lid)
                    if lote:
                        it["numero_lote"] = getattr(lote, "numero_lote", None)
                        it["bodega_nombre"] = getattr(getattr(lote, "bodega", None), "nombre", None)

        return ProductosPublicExtended(**cached_result)
    
    # Load related lote and bodega to avoid N+1 queries
    # JOIN Producto -> Lote -> Bodega to filter by sucursal
    stmt = (
        select(Producto)
        .join(Lote, Producto.id_lote == Lote.id_lote)
        .join(Bodega, Lote.id_bodega == Bodega.id_bodega)
        .options(selectinload(Producto.lote).selectinload(Lote.bodega))
    )
    
    # Apply sucursal filter if non-admin or admin with selection
    if sc_id_sucursal is not None:
        stmt = stmt.where(Bodega.id_sucursal == sc_id_sucursal)
    
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Producto.nombre_comercial.ilike(like))
            | (Producto.nombre_generico.ilike(like))
            | (Producto.codigo_interno.ilike(like))
            | (Producto.codigo_barras.ilike(like))
        )
    count = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    statement = stmt.offset(skip).limit(limit)
    productos = session.exec(statement).all()

    # Enrich productos with lote.numero_lote y bodega.nombre
    enriched: list[dict] = []
    for p in productos:
        p_dict = p.model_dump()
        numero_lote = None
        bodega_nombre = None
        # Prefer relationship if loaded, otherwise try to fetch by id_lote
        if getattr(p, "lote", None):
            numero_lote = getattr(p.lote, "numero_lote", None)
            if getattr(p.lote, "bodega", None):
                bodega_nombre = getattr(p.lote.bodega, "nombre", None)
        elif getattr(p, "id_lote", None):
            lote = session.get(Lote, p.id_lote)
            if lote:
                numero_lote = getattr(lote, "numero_lote", None)
                if getattr(lote, "id_bodega", None):
                    b = session.get(Bodega, lote.id_bodega)
                    bodega_nombre = getattr(b, "nombre", None) if b else None
        p_dict["numero_lote"] = numero_lote
        p_dict["bodega_nombre"] = bodega_nombre
        enriched.append(p_dict)

    result = ProductosPublicExtended(data=enriched, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get("/{id}", response_model=ProductoPublicExtended)
def read_producto(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get producto by ID, respecting sucursal scope.
    """
    # Get user scope
    scope = get_user_scope(current_user)
    sc_id_sucursal = scope.get("id_sucursal") if scope else None
    
    # Generate cache key
    cache_key = item_cache_key("productos", id)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return ProductoPublicExtended(**cached_result)
    
    # Load producto with relationships to guarantee lote and bodega availability
    # JOIN to validate sucursal scope
    stmt = (
        select(Producto)
        .join(Lote, Producto.id_lote == Lote.id_lote)
        .join(Bodega, Lote.id_bodega == Bodega.id_bodega)
        .options(selectinload(Producto.lote).selectinload(Lote.bodega))
        .where(Producto.id_producto == id)
    )
    
    # Apply sucursal filter for non-admin
    if sc_id_sucursal is not None:
        stmt = stmt.where(Bodega.id_sucursal == sc_id_sucursal)
    
    producto = session.exec(stmt).one_or_none()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")

    # Enrich with lote and bodega
    p_dict = producto.model_dump()
    numero_lote = None
    bodega_nombre = None
    if getattr(producto, "lote", None):
        numero_lote = getattr(producto.lote, "numero_lote", None)
        if getattr(producto.lote, "bodega", None):
            bodega_nombre = getattr(producto.lote.bodega, "nombre", None)
    elif getattr(producto, "id_lote", None):
        lote = session.get(Lote, producto.id_lote)
        if lote:
            numero_lote = getattr(lote, "numero_lote", None)
            if getattr(lote, "id_bodega", None):
                b = session.get(Bodega, lote.id_bodega)
                bodega_nombre = getattr(b, "nombre", None) if b else None
    p_dict["numero_lote"] = numero_lote
    p_dict["bodega_nombre"] = bodega_nombre

    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, p_dict, ttl=300)

    return p_dict



@router.get("/stats")
def read_productos_stats(
    session: SessionDep, 
    current_user: CurrentUser,
    id_sucursal: int | None = None,
) -> Any:
    """Retorna contadores simples para las cards del frontend, filtrados por sucursal.

    - total_productos: número de productos (estado=True)
    - stock_total: suma de cantidad_disponible
    - lotes_activos: lotes con estado 'Activo'
    - productos_criticos: productos con cantidad_disponible <= stock_minimo
    
    Admins can specify id_sucursal or see all. Non-admins see only their sucursal.
    """
    # Get user scope (None for admin, {"id_sucursal": X} for others)
    scope = get_user_scope(current_user)
    sc_id_sucursal = scope.get("id_sucursal") if scope else id_sucursal
    
    # Quick debug log to help trace 422 issues in development
    print(f"[debug] Enter read_productos_stats, sc_id_sucursal={sc_id_sucursal}", file=sys.stderr)
    logging.getLogger("uvicorn.error").info(f"Enter read_productos_stats, sc_id_sucursal={sc_id_sucursal}")

    try:
        # Build base queries with JOIN to Bodega for sucursal filtering
        # Total productos: JOIN Producto -> Lote -> Bodega
        stmt_total = (
            select(func.count(Producto.id_producto))
            .select_from(Producto)
            .join(Lote, Producto.id_lote == Lote.id_lote)
            .join(Bodega, Lote.id_bodega == Bodega.id_bodega)
            .where(Producto.estado == True)
        )
        if sc_id_sucursal is not None:
            stmt_total = stmt_total.where(Bodega.id_sucursal == sc_id_sucursal)
        
        # Stock total: sum cantidad_disponible with same filtering
        stmt_stock = (
            select(func.coalesce(func.sum(Producto.cantidad_disponible), 0))
            .select_from(Producto)
            .join(Lote, Producto.id_lote == Lote.id_lote)
            .join(Bodega, Lote.id_bodega == Bodega.id_bodega)
        )
        if sc_id_sucursal is not None:
            stmt_stock = stmt_stock.where(Bodega.id_sucursal == sc_id_sucursal)
        
        # Lotes activos: count from Lote filtered by bodega's sucursal
        stmt_lotes = (
            select(func.count(Lote.id_lote))
            .select_from(Lote)
            .join(Bodega, Lote.id_bodega == Bodega.id_bodega)
            .where(Lote.estado == "Activo")
        )
        if sc_id_sucursal is not None:
            stmt_lotes = stmt_lotes.where(Bodega.id_sucursal == sc_id_sucursal)
        
        # Productos críticos: cantidad_disponible <= stock_minimo
        stmt_criticos = (
            select(func.count(Producto.id_producto))
            .select_from(Producto)
            .join(Lote, Producto.id_lote == Lote.id_lote)
            .join(Bodega, Lote.id_bodega == Bodega.id_bodega)
            .where(Producto.cantidad_disponible <= Producto.stock_minimo)
        )
        if sc_id_sucursal is not None:
            stmt_criticos = stmt_criticos.where(Bodega.id_sucursal == sc_id_sucursal)
        
        # Execute queries
        total_productos_raw = session.exec(stmt_total).scalar_one_or_none()
        stock_total_raw = session.exec(stmt_stock).scalar_one_or_none()
        lotes_activos_raw = session.exec(stmt_lotes).scalar_one_or_none()
        productos_criticos_raw = session.exec(stmt_criticos).scalar_one_or_none()

        # Ensure integers
        total_productos = int(total_productos_raw or 0)
        stock_total = int(stock_total_raw or 0)
        lotes_activos = int(lotes_activos_raw or 0)
        productos_criticos = int(productos_criticos_raw or 0)

        return JSONResponse(status_code=200, content={
            "total_productos": total_productos,
            "stock_total": stock_total,
            "lotes_activos": lotes_activos,
            "productos_criticos": productos_criticos,
        })
    except Exception as e:
        # Log and return a safe default so frontend doesn't get 422
        logger = logging.getLogger("uvicorn.error")
        logger.exception("Failed to compute productos stats: %s", e)
        print("[error] Failed to compute productos stats:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse(status_code=200, content={
            "total_productos": 0,
            "stock_total": 0,
            "lotes_activos": 0,
            "productos_criticos": 0,
        })


@router.post("/", response_model=ProductoPublicExtended)
def create_producto(
    *, session: SessionDep, current_user: CurrentUser, producto_in: ProductoCreate
) -> Any:
    """
    Create new producto.
    """
    producto = Producto.model_validate(producto_in)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    
    # Invalidate cache
    invalidate_entity_cache("productos")

    # Enrich response with lote.numero_lote and bodega.nombre
    p_dict = producto.model_dump()
    numero_lote = None
    bodega_nombre = None
    if getattr(producto, 'id_lote', None):
        lote = session.get(Lote, producto.id_lote)
        if lote:
            numero_lote = getattr(lote, 'numero_lote', None)
            if getattr(lote, 'id_bodega', None):
                b = session.get(Bodega, lote.id_bodega)
                bodega_nombre = getattr(b, 'nombre', None) if b else None
    p_dict['numero_lote'] = numero_lote
    p_dict['bodega_nombre'] = bodega_nombre

    return p_dict


@router.put("/{id}", response_model=ProductoPublicExtended)
def update_producto(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    producto_in: ProductoUpdate,
) -> Any:
    """
    Update a producto.
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    update_dict = producto_in.model_dump(exclude_unset=True)
    producto.sqlmodel_update(update_dict)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    
    # Invalidate cache
    invalidate_entity_cache("productos")

    # Enrich response
    p_dict = producto.model_dump()
    numero_lote = None
    bodega_nombre = None
    if getattr(producto, 'id_lote', None):
        lote = session.get(Lote, producto.id_lote)
        if lote:
            numero_lote = getattr(lote, 'numero_lote', None)
            if getattr(lote, 'id_bodega', None):
                b = session.get(Bodega, lote.id_bodega)
                bodega_nombre = getattr(b, 'nombre', None) if b else None
    p_dict['numero_lote'] = numero_lote
    p_dict['bodega_nombre'] = bodega_nombre

    return p_dict


@router.delete("/{id}")
def delete_producto(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Delete a producto (soft delete).
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    producto.estado = False
    session.add(producto)
    session.commit()
    
    # Invalidate cache
    invalidate_entity_cache("productos")
    
    return Message(message="Producto deleted successfully")

