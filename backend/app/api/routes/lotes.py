from typing import Any
from datetime import date, datetime, timedelta
from pydantic import field_validator, model_validator
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import func, select, Session
from sqlalchemy import or_

from app.api.deps import CurrentUser, SessionDep, get_user_scope, ensure_bodega_in_scope, is_admin_user
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key, stats_cache_key,
    invalidate_stats_cache, invalidate_pattern
)
from app.models import (
    Lote,
    LoteCreate,
    LotePublic,
    LotesPublic,
    LotesStats,
    LoteUpdate,
    Message,
    Bodega,
    Producto,
    ProductoCreate,
    MovimientoInventario,
    Auditoria,
    Proveedor,
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


class DistribucionBodegaItem(SQLModel):
    """Items de productos para una bodega específica en recepción distribuida."""
    id_bodega: int
    items: list[RecepcionProductoItem]


class RecepcionDistribuidaPayload(SQLModel):
    """Payload para recepcionar un lote distribuyendo productos entre múltiples bodegas."""
    lote_base: LoteCreate
    distribuciones: list[DistribucionBodegaItem]


class CapacidadInsuficienteError(HTTPException):
    """Exception personalizada cuando bodega no tiene capacidad suficiente."""
    def __init__(self, bodega_id: int, bodega_nombre: str, disponible: int, requerido: int, sugerencias: dict):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "capacidad_insuficiente",
                "bodega_id": bodega_id,
                "bodega_nombre": bodega_nombre,
                "capacidad_disponible": disponible,
                "capacidad_requerida": requerido,
                "excedente": requerido - disponible,
                "sugerencias_distribucion": sugerencias
            }
        )


router = APIRouter(prefix="/lotes", tags=["lotes"])


# ============================================================================
# FUNCIONES AUXILIARES PARA VALIDACIÓN DE CAPACIDAD DE BODEGAS
# ============================================================================

def calcular_ocupacion_bodega(session: Session, bodega_id: int) -> int:
    """
    Calcula la ocupación actual de una bodega sumando cantidad_total
    de todos los productos en lotes activos de esa bodega.
    
    Usa lock de bodega para prevenir race conditions sin usar FOR UPDATE en agregación.
    
    Args:
        session: Sesión de base de datos
        bodega_id: ID de la bodega
        
    Returns:
        Ocupación actual en unidades
    """
    # 🔒 Obtener lock de la bodega (lock a nivel de fila, no de agregación)
    # Esto previene que otra transacción modifique la bodega mientras calculamos
    bodega_lock_stmt = select(Bodega).where(Bodega.id_bodega == bodega_id).with_for_update()
    session.exec(bodega_lock_stmt).one()  # Lock acquired
    
    # Ahora calculamos ocupación sin lock (ya tenemos lock de bodega)
    stmt = (
        select(func.coalesce(func.sum(Producto.cantidad_total), 0))
        .join(Lote, Producto.id_lote == Lote.id_lote)
        .where(
            Lote.id_bodega == bodega_id,
            Lote.estado.in_(["Activo", "En tránsito"])  # Estados que ocupan espacio físico
        )
    )
    
    ocupacion = session.exec(stmt).one()
    return int(ocupacion)


def obtener_bodegas_alternativas(
    session: Session, 
    bodega_principal_id: int,
    cantidad_excedente: int,
    current_user: CurrentUser
) -> list[dict]:
    """
    Encuentra bodegas de la misma sucursal con capacidad disponible.
    
    Args:
        session: Sesión de base de datos
        bodega_principal_id: ID de la bodega que no tiene capacidad
        cantidad_excedente: Cantidad que excede la capacidad
        current_user: Usuario actual (para validar alcance)
        
    Returns:
        Lista de bodegas ordenadas por capacidad disponible (descendente)
    """
    bodega_principal = session.get(Bodega, bodega_principal_id)
    if not bodega_principal:
        return []
    
    # Buscar bodegas activas de la misma sucursal (excluyendo la principal)
    stmt = (
        select(Bodega)
        .where(
            Bodega.id_sucursal == bodega_principal.id_sucursal,
            Bodega.id_bodega != bodega_principal_id,
            Bodega.estado == True
        )
    )
    
    bodegas = session.exec(stmt).all()
    
    sugerencias = []
    for bodega in bodegas:
        ocupacion = calcular_ocupacion_bodega(session, bodega.id_bodega)
        disponible = bodega.capacidad - ocupacion
        
        if disponible > 0:
            sugerencias.append({
                "id_bodega": bodega.id_bodega,
                "nombre": bodega.nombre,
                "tipo": bodega.tipo,
                "capacidad_total": bodega.capacidad,
                "ocupacion_actual": ocupacion,
                "capacidad_disponible": disponible,
                "puede_recibir": min(disponible, cantidad_excedente),
                "porcentaje_ocupacion": round((ocupacion / bodega.capacidad * 100), 2) if bodega.capacidad > 0 else 0
            })
    
    # Ordenar por capacidad disponible (mayor primero) para optimizar logística
    sugerencias.sort(key=lambda x: x["capacidad_disponible"], reverse=True)
    
    return sugerencias


def sugerir_distribucion_automatica(
    sugerencias: list[dict],
    cantidad_excedente: int
) -> tuple[list[dict], int]:
    """
    Algoritmo greedy para distribuir excedente entre bodegas disponibles.
    
    Estrategia: Llenar bodegas de mayor capacidad primero para minimizar
    el número de bodegas involucradas (reduce complejidad logística).
    
    Args:
        sugerencias: Lista de bodegas alternativas con capacidad
        cantidad_excedente: Cantidad total a distribuir
        
    Returns:
        Tupla (distribución_propuesta, cantidad_restante)
        - distribución_propuesta: Lista de asignaciones por bodega
        - cantidad_restante: Cantidad que no pudo asignarse (0 si todo cabe)
    """
    distribucion = []
    restante = cantidad_excedente
    
    for bodega in sugerencias:
        if restante <= 0:
            break
        
        cantidad_asignar = min(bodega["puede_recibir"], restante)
        distribucion.append({
            "id_bodega": bodega["id_bodega"],
            "nombre_bodega": bodega["nombre"],
            "tipo": bodega["tipo"],
            "cantidad": cantidad_asignar,
            "porcentaje_ocupacion_resultante": round(
                ((bodega["ocupacion_actual"] + cantidad_asignar) / bodega["capacidad_total"] * 100), 2
            )
        })
        restante -= cantidad_asignar
    
    return distribucion, restante


# ============================================================================
# ENDPOINTS DE LOTES
# ============================================================================

@router.get("/", response_model=LotesPublic)
def read_lotes(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    estado: str | None = None,
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
        estado=estado,
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
    
    # Build base query with joins para incluir proveedor y bodega
    # Usamos outerjoin para manejar lotes sin bodega o sin proveedor
    base_stmt = (
        select(
            Lote,
            Proveedor.nombre.label("proveedor_nombre"),  # type: ignore
            Bodega.nombre.label("bodega_nombre"),  # type: ignore
        )
        .outerjoin(Proveedor, Proveedor.id_proveedor == Lote.id_proveedor)
        .outerjoin(Bodega, Bodega.id_bodega == Lote.id_bodega)
    )

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
    if estado:
        base_stmt = base_stmt.where(Lote.estado == estado)
    if q:
        base_stmt = base_stmt.where(Lote.numero_lote.contains(q))
    if fecha_desde is not None:
        base_stmt = base_stmt.where(Lote.fecha_registro >= datetime.combine(fecha_desde, datetime.min.time()))
    if fecha_hasta is not None:
        base_stmt = base_stmt.where(Lote.fecha_registro <= datetime.combine(fecha_hasta, datetime.max.time()))

    # Contar lotes aplicando los mismos filtros (sin los campos adicionales del join)
    count_stmt = select(Lote).outerjoin(Bodega, Bodega.id_bodega == Lote.id_bodega)
    
    if sc_id_sucursal is not None:
        count_stmt = count_stmt.where(
            or_(
                Bodega.id_sucursal == sc_id_sucursal,  # type: ignore[attr-defined]
                Lote.id_bodega.is_(None)  # type: ignore[attr-defined]
            )
        )
    if id_bodega is not None:
        count_stmt = count_stmt.where(Lote.id_bodega == id_bodega)
    if id_proveedor is not None:
        count_stmt = count_stmt.where(Lote.id_proveedor == id_proveedor)
    if estado:
        count_stmt = count_stmt.where(Lote.estado == estado)
    if q:
        count_stmt = count_stmt.where(Lote.numero_lote.contains(q))
    if fecha_desde is not None:
        count_stmt = count_stmt.where(Lote.fecha_registro >= datetime.combine(fecha_desde, datetime.min.time()))
    if fecha_hasta is not None:
        count_stmt = count_stmt.where(Lote.fecha_registro <= datetime.combine(fecha_hasta, datetime.max.time()))
    
    count = session.exec(select(func.count()).select_from(count_stmt.subquery())).one()
    
    # Ejecutar consulta principal con offset y limit
    results = session.exec(base_stmt.offset(skip).limit(limit)).all()
    
    # Extraer lotes y obtener IDs para consultar productos en batch
    lotes_result = []
    lote_ids: list[int] = []
    proveedores_map: dict[int, str] = {}
    bodegas_map: dict[int, str] = {}
    
    for row in results:
        # row es una tupla: (Lote, proveedor_nombre, bodega_nombre)
        lote = row[0]
        proveedor_nombre = row[1] if len(row) > 1 and row[1] else None
        bodega_nombre = row[2] if len(row) > 2 and row[2] else None
        
        lotes_result.append((lote, proveedor_nombre, bodega_nombre))
        lote_ids.append(lote.id_lote)  # type: ignore
        
        if proveedor_nombre and lote.id_proveedor:
            proveedores_map[lote.id_proveedor] = proveedor_nombre  # type: ignore
        if bodega_nombre and lote.id_bodega:
            bodegas_map[lote.id_bodega] = bodega_nombre  # type: ignore
    
    # Obtener todos los productos de los lotes en una sola consulta (solo si hay lotes)
    productos_por_lote: dict[int, list[Producto]] = {}
    if lote_ids:
        productos_stmt = select(Producto).where(Producto.id_lote.in_(lote_ids))  # type: ignore
        productos_list = session.exec(productos_stmt).all()
        
        # Crear diccionario de productos por lote
        for producto in productos_list:
            if producto.id_lote not in productos_por_lote:
                productos_por_lote[producto.id_lote] = []
            productos_por_lote[producto.id_lote].append(producto)
    
    # Enriquecer lotes con datos relacionados
    lotes_enriquecidos = []
    for lote, proveedor_nombre, bodega_nombre in lotes_result:
        # Obtener productos del lote desde el diccionario
        productos = productos_por_lote.get(lote.id_lote, [])  # type: ignore
        
        producto_nombre = None
        stock_total = 0
        if productos:
            # Usar el nombre del primer producto como referencia
            producto_nombre = productos[0].nombre_comercial if productos else None
            # Sumar el stock total de todos los productos
            stock_total = sum(p.cantidad_disponible for p in productos)
        
        # Crear objeto enriquecido
        lote_dict = lote.model_dump()
        lote_dict["proveedor_nombre"] = proveedor_nombre
        lote_dict["bodega_nombre"] = bodega_nombre
        lote_dict["producto_nombre"] = producto_nombre
        lote_dict["stock_total"] = stock_total
        
        lotes_enriquecidos.append(LotePublic(**lote_dict))
    
    result = LotesPublic(data=lotes_enriquecidos, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)
    
    return result


@router.get(
    "/stats",
    response_model=LotesStats
)
def get_lotes_stats(
    session: SessionDep,
    current_user: CurrentUser
) -> LotesStats:
    """
    Get lotes statistics.
    Returns total lotes, activos, vencidos, and próximos a vencer.
    """
    try:
        scope = get_user_scope(current_user)
        sc_id_sucursal = scope.get("id_sucursal") if scope is not None else None
        
        # Generate cache key with scope
        cache_key = stats_cache_key(f"lotes:{sc_id_sucursal or 'all'}")
        
        # Try to get from cache
        cached_result = get_cache(cache_key)
        if cached_result is not None:
            return LotesStats(**cached_result)
        
        fecha_hoy = date.today()
        dias_vencimiento = 30  # Días para considerar "próximos a vencer"
        fecha_limite = fecha_hoy + timedelta(days=dias_vencimiento)
        
        # Build base query with scope filtering - usar outerjoin para incluir lotes sin bodega
        base_stmt = select(Lote).outerjoin(Bodega, Bodega.id_bodega == Lote.id_bodega)
        
        if sc_id_sucursal is not None:
            # Si no es admin, filtrar por sucursal o lotes sin bodega
            base_stmt = base_stmt.where(
                or_(
                    Bodega.id_sucursal == sc_id_sucursal,  # type: ignore[attr-defined]
                    Lote.id_bodega.is_(None)  # type: ignore[attr-defined]
                )
            )
        
        # Obtener todos los lotes con el filtro de scope
        lotes = session.exec(base_stmt).all()
        
        # Total lotes: contar todos los lotes que pasan el filtro de scope
        total_lotes = len(lotes)
        
        # Lotes activos: estado == "Activo" Y fecha_vencimiento >= hoy
        activos = sum(
            1 for lote in lotes 
            if lote.estado == "Activo" and lote.fecha_vencimiento >= fecha_hoy
        )
        
        # Lotes vencidos: fecha_vencimiento < hoy (independientemente del estado)
        vencidos = sum(
            1 for lote in lotes 
            if lote.fecha_vencimiento < fecha_hoy
        )
        
        # Lotes próximos a vencer: activos que vencen en menos de X días (entre hoy y fecha_limite)
        proximos_a_vencer = sum(
            1 for lote in lotes 
            if lote.estado == "Activo" 
            and fecha_hoy < lote.fecha_vencimiento <= fecha_limite
        )
        
        result = LotesStats(
            total_lotes=int(total_lotes),
            activos=int(activos),
            vencidos=int(vencidos),
            proximos_a_vencer=int(proximos_a_vencer)
        )
        
        # Cache the result (TTL: 1 minute - stats change frequently)
        set_cache(cache_key, result.model_dump(), ttl=60)
        
        return result
    except Exception as e:
        # Log error for debugging
        print(f"Error in get_lotes_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


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
    # Validate fecha_vencimiento > fecha_fabricacion
    if lote_in.fecha_vencimiento <= lote_in.fecha_fabricacion:
        raise HTTPException(
            status_code=422,
            detail="fecha_vencimiento must be greater than fecha_fabricacion"
        )
    
    # Validate that proveedor exists
    from app.models import Proveedor
    proveedor = session.get(Proveedor, lote_in.id_proveedor)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    
    # Validate that bodega exists (if provided)
    if lote_in.id_bodega is not None:
        bodega = session.get(Bodega, lote_in.id_bodega)
        if not bodega:
            raise HTTPException(status_code=404, detail="Bodega not found")
        # Validar alcance de bodega
        ensure_bodega_in_scope(session, lote_in.id_bodega, current_user)
    
    # Check if numero_lote already exists (if provided)
    if lote_in.numero_lote:
        existing_lote = session.exec(
            select(Lote).where(Lote.numero_lote == lote_in.numero_lote)
        ).first()
        if existing_lote:
            raise HTTPException(
                status_code=400,
                detail="A lote with this numero_lote already exists"
            )
    
    lote = Lote.model_validate(lote_in)
    session.add(lote)
    session.commit()
    session.refresh(lote)
    
    # Invalidate cache
    invalidate_entity_cache("lotes")
    invalidate_stats_cache("lotes")
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
    """
    Recepciona un lote de productos con validación de capacidad de bodega.
    
    Si la bodega no tiene capacidad suficiente, retorna 409 Conflict con
    sugerencias de distribución automática a otras bodegas de la misma sucursal.
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="La recepción debe incluir productos")

    # Validaciones de fechas
    if payload.lote.fecha_fabricacion > payload.lote.fecha_vencimiento:
        raise HTTPException(status_code=400, detail="Fecha de fabricación no puede ser mayor a vencimiento")

    # Verificar alcance de bodega
    if payload.lote.id_bodega is not None:
        ensure_bodega_in_scope(session, payload.lote.id_bodega, current_user)
    else:
        raise HTTPException(status_code=400, detail="Debe especificar una bodega para la recepción")

    # ========================================================================
    # 🔍 VALIDACIÓN DE CAPACIDAD DE BODEGA
    # ========================================================================
    bodega = session.get(Bodega, payload.lote.id_bodega)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")
    
    # Calcular cantidad total del lote a recepcionar
    cantidad_total_lote = sum(item.cantidad for item in payload.items)
    
    # Calcular ocupación actual con lock para prevenir race conditions
    ocupacion_actual = calcular_ocupacion_bodega(session, bodega.id_bodega)
    capacidad_disponible = bodega.capacidad - ocupacion_actual
    
    # Si excede capacidad, generar sugerencias y retornar error 409
    if cantidad_total_lote > capacidad_disponible:
        excedente = cantidad_total_lote - capacidad_disponible
        
        # Buscar bodegas alternativas en la misma sucursal
        bodegas_alternativas = obtener_bodegas_alternativas(
            session, 
            bodega.id_bodega, 
            excedente,
            current_user
        )
        
        # Sugerir distribución automática
        distribucion, restante = sugerir_distribucion_automatica(bodegas_alternativas, excedente)
        
        if restante > 0:
            # No hay suficiente capacidad en toda la sucursal - retornar mensaje amigable
            capacidad_total_sucursal = sum(b["capacidad_disponible"] for b in bodegas_alternativas) + capacidad_disponible
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "capacidad_insuficiente_sucursal",
                    "message": "Por favor utiliza otra bodega con espacio disponible. La sucursal no tiene capacidad suficiente para este lote.",
                    "bodega_seleccionada": bodega.nombre,
                    "capacidad_disponible_sucursal": capacidad_total_sucursal,
                    "capacidad_requerida": cantidad_total_lote,
                    "deficit": restante,
                    "sugerencia": f"Necesitas {restante} unidades más de espacio. Considera usar otra bodega o dividir el lote."
                }
            )
        
        # Retornar 409 con sugerencias de distribución
        raise CapacidadInsuficienteError(
            bodega_id=bodega.id_bodega,
            bodega_nombre=bodega.nombre,
            disponible=capacidad_disponible,
            requerido=cantidad_total_lote,
            sugerencias={
                "bodega_principal": {
                    "id_bodega": bodega.id_bodega,
                    "nombre": bodega.nombre,
                    "tipo": bodega.tipo,
                    "capacidad_disponible": capacidad_disponible,
                    "cantidad_sugerida": capacidad_disponible,
                    "ocupacion_actual": ocupacion_actual,
                    "capacidad_total": bodega.capacidad
                },
                "bodegas_secundarias": distribucion,
                "mensaje": f"Se sugiere distribuir {capacidad_disponible} unidades en '{bodega.nombre}' y el resto en otras bodegas."
            }
        )
    
    # ========================================================================
    # ✅ HAY CAPACIDAD SUFICIENTE - PROCEDER CON RECEPCIÓN NORMAL
    # ========================================================================
    
    # Generar número de lote automático único
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
    # Invalidar stats cache (el patrón puede variar por scope, invalidar todo)
    invalidate_pattern("lotes:*:stats")
    invalidate_stats_cache("lotes")  # También invalidar la clave sin scope por si acaso
    invalidate_entity_cache("productos")

    return {"lote": lote, "productos_ids": productos_ids}


@router.post("/recepcion-distribuida")
def recepcion_lote_distribuida(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    payload: RecepcionDistribuidaPayload
) -> Any:
    """
    Recepciona un lote distribuyendo productos entre múltiples bodegas de la misma sucursal.
    
    Este endpoint se usa cuando una bodega no tiene capacidad suficiente y se necesita
    distribuir el lote entre varias bodegas.
    
    Crea sub-lotes (uno por bodega) con el mismo número base pero sufijos diferentes.
    Usa transacción atómica para garantizar consistencia.
    
    Returns:
        Diccionario con número de lote base y lista de productos creados por bodega
    """
    if not payload.distribuciones:
        raise HTTPException(status_code=400, detail="Debe especificar al menos una bodega")
    
    # Validaciones de fechas del lote base
    if payload.lote_base.fecha_fabricacion > payload.lote_base.fecha_vencimiento:
        raise HTTPException(status_code=400, detail="Fecha de fabricación no puede ser mayor a vencimiento")
    
    # Validar que todas las bodegas están en el alcance del usuario
    bodega_ids = [d.id_bodega for d in payload.distribuciones]
    for bodega_id in bodega_ids:
        ensure_bodega_in_scope(session, bodega_id, current_user)
    
    # Obtener todas las bodegas y validar que existan
    bodegas = session.exec(select(Bodega).where(Bodega.id_bodega.in_(bodega_ids))).all()
    if len(bodegas) != len(bodega_ids):
        raise HTTPException(status_code=404, detail="Una o más bodegas no existen")
    
    # Validar que todas las bodegas son de la misma sucursal
    sucursales = set(b.id_sucursal for b in bodegas)
    if len(sucursales) > 1:
        raise HTTPException(
            status_code=400, 
            detail="Todas las bodegas deben pertenecer a la misma sucursal"
        )
    
    # ========================================================================
    # 🔍 RE-VALIDAR CAPACIDAD DE CADA BODEGA CON LOCKS
    # ========================================================================
    for dist in payload.distribuciones:
        bodega = next((b for b in bodegas if b.id_bodega == dist.id_bodega), None)
        if not bodega:
            continue
        
        cantidad_asignada = sum(item.cantidad for item in dist.items)
        ocupacion = calcular_ocupacion_bodega(session, bodega.id_bodega)
        disponible = bodega.capacidad - ocupacion
        
        if cantidad_asignada > disponible:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "capacidad_insuficiente_al_distribuir",
                    "message": f"Bodega '{bodega.nombre}' ya no tiene capacidad suficiente.",
                    "bodega": bodega.nombre,
                    "disponible": disponible,
                    "requerido": cantidad_asignada,
                    "sugerencia": "La capacidad pudo haber cambiado. Recalcula la distribución."
                }
            )
    
    # ========================================================================
    # ✅ CREAR SUB-LOTES Y PRODUCTOS EN CADA BODEGA
    # ========================================================================
    
    # Generar número base para el lote (usaremos la primera bodega como referencia)
    numero_lote_base = generar_numero_lote_unico(
        session, 
        bodega_ids[0], 
        payload.lote_base.id_proveedor
    )
    
    productos_creados = []
    lotes_creados = []
    
    # Crear sub-lote por cada bodega
    for dist in payload.distribuciones:
        bodega = next(b for b in bodegas if b.id_bodega == dist.id_bodega)
        
        # Crear sub-lote con sufijo identificador de bodega
        lote_data = payload.lote_base.model_dump(exclude_none=True)
        lote_data["numero_lote"] = f"{numero_lote_base}-{bodega.nombre[:3].upper()}"
        lote_data["id_bodega"] = dist.id_bodega
        lote_data["observaciones"] = (
            f"Distribución automática. Lote base: {numero_lote_base}. "
            f"{lote_data.get('observaciones', '')}"
        ).strip()
        
        lote = Lote.model_validate(lote_data)
        session.add(lote)
        session.commit()
        session.refresh(lote)
        
        lotes_creados.append({
            "id_lote": lote.id_lote,
            "numero_lote": lote.numero_lote,
            "bodega": bodega.nombre
        })
        
        # Crear productos para este sub-lote
        for item in dist.items:
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
            
            productos_creados.append({
                "id_producto": prod.id_producto,
                "nombre": prod.nombre_comercial,
                "cantidad": prod.cantidad_total,
                "bodega_id": bodega.id_bodega,
                "bodega_nombre": bodega.nombre,
                "numero_lote": lote.numero_lote
            })
            
            # Crear movimiento de inventario
            movimiento = MovimientoInventario(
                tipo_movimiento="Entrada",
                cantidad=item.cantidad,
                descripcion=f"Recepción distribuida - Lote base {numero_lote_base} → {bodega.nombre}",
                id_producto=prod.id_producto,  # type: ignore[arg-type]
                id_usuario=current_user.id,  # type: ignore[arg-type]
                id_sucursal_origen=None,
                id_sucursal_destino=bodega.id_sucursal,
            )
            session.add(movimiento)
            session.commit()
    
    # ========================================================================
    # 📝 AUDITORÍA
    # ========================================================================
    audit = Auditoria(
        entidad_afectada="lote",
        id_registro_afectado=numero_lote_base,
        accion="recepcion_lote_distribuida",
        detalle={
            "numero_lote_base": numero_lote_base,
            "lotes_creados": lotes_creados,
            "total_productos": len(productos_creados),
            "bodegas_involucradas": len(payload.distribuciones),
        },
        resultado="Éxito",
        id_usuario=current_user.id,  # type: ignore[arg-type]
    )
    session.add(audit)
    session.commit()
    
    # Invalidar caches
    invalidate_entity_cache("lotes")
    invalidate_entity_cache("productos")
    invalidate_pattern("lotes:*:stats")
    invalidate_stats_cache("lotes")
    
    return {
        "numero_lote_base": numero_lote_base,
        "lotes_creados": lotes_creados,
        "productos_creados": productos_creados,
        "total_productos": len(productos_creados),
        "bodegas_utilizadas": len(payload.distribuciones),
        "message": f"✅ Lote distribuido exitosamente en {len(payload.distribuciones)} bodega(s)"
    }


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
    
    # Validar alcance
    if not is_admin_user(current_user):
        bodega = session.get(Bodega, lote.id_bodega)
        if not bodega or bodega.id_sucursal != current_user.id_sucursal:
            raise HTTPException(status_code=404, detail="Lote not found")
    
    update_dict = lote_in.model_dump(exclude_unset=True)
    
    # Validate fecha_vencimiento > fecha_fabricacion if both are being updated
    fecha_fabricacion = update_dict.get("fecha_fabricacion") or lote.fecha_fabricacion
    fecha_vencimiento = update_dict.get("fecha_vencimiento") or lote.fecha_vencimiento
    
    if fecha_vencimiento <= fecha_fabricacion:
        raise HTTPException(
            status_code=422,
            detail="fecha_vencimiento must be greater than fecha_fabricacion"
        )
    
    # Validate proveedor exists if being updated
    if "id_proveedor" in update_dict:
        from app.models import Proveedor
        proveedor = session.get(Proveedor, update_dict["id_proveedor"])
        if not proveedor:
            raise HTTPException(status_code=404, detail="Proveedor not found")
    
    # Validate bodega exists if being updated
    if "id_bodega" in update_dict and update_dict["id_bodega"] is not None:
        bodega = session.get(Bodega, update_dict["id_bodega"])
        if not bodega:
            raise HTTPException(status_code=404, detail="Bodega not found")
        # Validar alcance de bodega
        ensure_bodega_in_scope(session, update_dict["id_bodega"], current_user)
    
    # Check if numero_lote already exists (if being updated)
    if "numero_lote" in update_dict and update_dict["numero_lote"] and update_dict["numero_lote"] != lote.numero_lote:
        existing_lote = session.exec(
            select(Lote).where(Lote.numero_lote == update_dict["numero_lote"])
        ).first()
        if existing_lote:
            raise HTTPException(
                status_code=400,
                detail="A lote with this numero_lote already exists"
            )
    
    lote.sqlmodel_update(update_dict)
    session.add(lote)
    session.commit()
    session.refresh(lote)
    
    # Invalidate cache
    invalidate_entity_cache("lotes")
    invalidate_stats_cache("lotes")
    invalidate_entity_cache("proveedores")  # Stats may change
    
    return lote

