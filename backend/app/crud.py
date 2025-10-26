import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Auditoria,
    AuditoriaCreate,
    AuditoriaUpdate,
    Bodega,
    BodegaCreate,
    BodegaUpdate,
    Item,
    ItemCreate,
    Lote,
    LoteCreate,
    LoteUpdate,
    MovimientoInventario,
    MovimientoInventarioCreate,
    MovimientoInventarioUpdate,
    Producto,
    ProductoCreate,
    ProductoUpdate,
    Proveedor,
    ProveedorCreate,
    ProveedorUpdate,
    Rol,
    RolCreate,
    RolUpdate,
    Sucursal,
    SucursalCreate,
    SucursalUpdate,
    User,
    UserCreate,
    UserCreateByAdmin,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    # Crear el usuario sin relaciones
    user_data = user_create.model_dump(exclude_unset=True, exclude={"password"})
    user_data["hashed_password"] = get_password_hash(user_create.password)
    db_obj = User(**user_data)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def create_user_by_admin(*, session: Session, user_in: UserCreateByAdmin) -> User:
    """Crear un nuevo usuario por un administrador con validación de rol y sucursal."""
    # Validar que el rol existe
    rol = session.get(Rol, user_in.id_rol)
    if not rol:
        raise ValueError(f"El rol con ID {user_in.id_rol} no existe")
    
    # Validar que el rol es Auxiliar (ID 3) o Auditor (ID 4)
    if user_in.id_rol not in [3, 4]:
        raise ValueError("Solo se pueden asignar roles de Auxiliar (ID: 3) o Auditor (ID: 4)")
    
    # Validar sucursal si se proporciona
    if user_in.id_sucursal:
        sucursal = session.get(Sucursal, user_in.id_sucursal)
        if not sucursal:
            raise ValueError(f"La sucursal con ID {user_in.id_sucursal} no existe")
    
    # Crear el usuario
    user_data = user_in.model_dump(exclude_unset=True)
    user_data["hashed_password"] = get_password_hash(user_in.password)
    db_obj = User(**user_data)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# =============================================================================
# CRUD PARA SISTEMA DE INVENTARIO FARMACÉUTICO
# =============================================================================

# -----------------------------------------------------------------------------
# SUCURSAL
# -----------------------------------------------------------------------------
def create_sucursal(*, session: Session, sucursal_in: SucursalCreate) -> Sucursal:
    """Crear una nueva sucursal."""
    db_obj = Sucursal.model_validate(sucursal_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_sucursal(*, session: Session, sucursal_id: int) -> Sucursal | None:
    """Obtener una sucursal por ID."""
    statement = select(Sucursal).where(Sucursal.id_sucursal == sucursal_id)
    return session.exec(statement).first()


def get_sucursales(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[Sucursal]:
    """Obtener lista de sucursales con paginación."""
    statement = select(Sucursal).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_sucursal(
    *, session: Session, db_sucursal: Sucursal, sucursal_in: SucursalUpdate
) -> Sucursal:
    """Actualizar una sucursal existente."""
    sucursal_data = sucursal_in.model_dump(exclude_unset=True)
    db_sucursal.sqlmodel_update(sucursal_data)
    session.add(db_sucursal)
    session.commit()
    session.refresh(db_sucursal)
    return db_sucursal


def delete_sucursal(*, session: Session, sucursal_id: int) -> bool:
    """Soft delete: marcar sucursal como inactiva."""
    sucursal = get_sucursal(session=session, sucursal_id=sucursal_id)
    if sucursal:
        sucursal.estado = False
        session.add(sucursal)
        session.commit()
        return True
    return False


# -----------------------------------------------------------------------------
# BODEGA
# -----------------------------------------------------------------------------
def create_bodega(*, session: Session, bodega_in: BodegaCreate) -> Bodega:
    """Crear una nueva bodega."""
    db_obj = Bodega.model_validate(bodega_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_bodega(*, session: Session, bodega_id: int) -> Bodega | None:
    """Obtener una bodega por ID."""
    statement = select(Bodega).where(Bodega.id_bodega == bodega_id)
    return session.exec(statement).first()


def get_bodegas(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[Bodega]:
    """Obtener lista de bodegas con paginación."""
    statement = select(Bodega).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_bodegas_by_sucursal(
    *, session: Session, sucursal_id: int, skip: int = 0, limit: int = 100
) -> list[Bodega]:
    """Obtener bodegas de una sucursal específica."""
    statement = (
        select(Bodega)
        .where(Bodega.id_sucursal == sucursal_id)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def update_bodega(
    *, session: Session, db_bodega: Bodega, bodega_in: BodegaUpdate
) -> Bodega:
    """Actualizar una bodega existente."""
    bodega_data = bodega_in.model_dump(exclude_unset=True)
    db_bodega.sqlmodel_update(bodega_data)
    session.add(db_bodega)
    session.commit()
    session.refresh(db_bodega)
    return db_bodega


def delete_bodega(*, session: Session, bodega_id: int) -> bool:
    """Soft delete: marcar bodega como inactiva."""
    bodega = get_bodega(session=session, bodega_id=bodega_id)
    if bodega:
        bodega.estado = False
        session.add(bodega)
        session.commit()
        return True
    return False


# -----------------------------------------------------------------------------
# PROVEEDOR
# -----------------------------------------------------------------------------
def create_proveedor(*, session: Session, proveedor_in: ProveedorCreate) -> Proveedor:
    """Crear un nuevo proveedor."""
    db_obj = Proveedor.model_validate(proveedor_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_proveedor(*, session: Session, proveedor_id: int) -> Proveedor | None:
    """Obtener un proveedor por ID."""
    statement = select(Proveedor).where(Proveedor.id_proveedor == proveedor_id)
    return session.exec(statement).first()


def get_proveedor_by_nit(*, session: Session, nit: str) -> Proveedor | None:
    """Obtener un proveedor por NIT."""
    statement = select(Proveedor).where(Proveedor.nit == nit)
    return session.exec(statement).first()


def get_proveedores(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[Proveedor]:
    """Obtener lista de proveedores con paginación."""
    statement = select(Proveedor).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_proveedor(
    *, session: Session, db_proveedor: Proveedor, proveedor_in: ProveedorUpdate
) -> Proveedor:
    """Actualizar un proveedor existente."""
    proveedor_data = proveedor_in.model_dump(exclude_unset=True)
    db_proveedor.sqlmodel_update(proveedor_data)
    session.add(db_proveedor)
    session.commit()
    session.refresh(db_proveedor)
    return db_proveedor


def delete_proveedor(*, session: Session, proveedor_id: int) -> bool:
    """Soft delete: marcar proveedor como inactivo."""
    proveedor = get_proveedor(session=session, proveedor_id=proveedor_id)
    if proveedor:
        proveedor.estado = False
        session.add(proveedor)
        session.commit()
        return True
    return False


# -----------------------------------------------------------------------------
# LOTE
# -----------------------------------------------------------------------------
def create_lote(*, session: Session, lote_in: LoteCreate) -> Lote:
    """Crear un nuevo lote."""
    db_obj = Lote.model_validate(lote_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_lote(*, session: Session, lote_id: int) -> Lote | None:
    """Obtener un lote por ID."""
    statement = select(Lote).where(Lote.id_lote == lote_id)
    return session.exec(statement).first()


def get_lote_by_numero(*, session: Session, numero_lote: str) -> Lote | None:
    """Obtener un lote por número."""
    statement = select(Lote).where(Lote.numero_lote == numero_lote)
    return session.exec(statement).first()


def get_lotes(*, session: Session, skip: int = 0, limit: int = 100) -> list[Lote]:
    """Obtener lista de lotes con paginación."""
    statement = select(Lote).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_lotes_by_bodega(
    *, session: Session, bodega_id: int, skip: int = 0, limit: int = 100
) -> list[Lote]:
    """Obtener lotes de una bodega específica."""
    statement = (
        select(Lote).where(Lote.id_bodega == bodega_id).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


def get_lotes_by_proveedor(
    *, session: Session, proveedor_id: int, skip: int = 0, limit: int = 100
) -> list[Lote]:
    """Obtener lotes de un proveedor específico."""
    statement = (
        select(Lote).where(Lote.id_proveedor == proveedor_id).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


def update_lote(*, session: Session, db_lote: Lote, lote_in: LoteUpdate) -> Lote:
    """Actualizar un lote existente."""
    lote_data = lote_in.model_dump(exclude_unset=True)
    db_lote.sqlmodel_update(lote_data)
    session.add(db_lote)
    session.commit()
    session.refresh(db_lote)
    return db_lote


# -----------------------------------------------------------------------------
# PRODUCTO
# -----------------------------------------------------------------------------
def create_producto(*, session: Session, producto_in: ProductoCreate) -> Producto:
    """Crear un nuevo producto."""
    db_obj = Producto.model_validate(producto_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_producto(*, session: Session, producto_id: int) -> Producto | None:
    """Obtener un producto por ID."""
    statement = select(Producto).where(Producto.id_producto == producto_id)
    return session.exec(statement).first()


def get_producto_by_codigo_interno(
    *, session: Session, codigo_interno: str
) -> Producto | None:
    """Obtener un producto por código interno."""
    statement = select(Producto).where(Producto.codigo_interno == codigo_interno)
    return session.exec(statement).first()


def get_producto_by_codigo_barras(
    *, session: Session, codigo_barras: str
) -> Producto | None:
    """Obtener un producto por código de barras."""
    statement = select(Producto).where(Producto.codigo_barras == codigo_barras)
    return session.exec(statement).first()


def get_productos(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[Producto]:
    """Obtener lista de productos con paginación."""
    statement = select(Producto).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_productos_by_lote(
    *, session: Session, lote_id: int, skip: int = 0, limit: int = 100
) -> list[Producto]:
    """Obtener productos de un lote específico."""
    statement = (
        select(Producto).where(Producto.id_lote == lote_id).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


def get_productos_bajo_stock(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[Producto]:
    """Obtener productos con stock por debajo del mínimo."""
    statement = (
        select(Producto)
        .where(Producto.cantidad_disponible <= Producto.stock_minimo)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def update_producto(
    *, session: Session, db_producto: Producto, producto_in: ProductoUpdate
) -> Producto:
    """Actualizar un producto existente."""
    producto_data = producto_in.model_dump(exclude_unset=True)
    db_producto.sqlmodel_update(producto_data)
    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    return db_producto


def delete_producto(*, session: Session, producto_id: int) -> bool:
    """Soft delete: marcar producto como inactivo."""
    producto = get_producto(session=session, producto_id=producto_id)
    if producto:
        producto.estado = False
        session.add(producto)
        session.commit()
        return True
    return False


def ajustar_stock_producto(
    *, session: Session, producto_id: int, cantidad: int, es_suma: bool = True
) -> Producto | None:
    """Ajustar el stock disponible de un producto."""
    producto = get_producto(session=session, producto_id=producto_id)
    if producto:
        if es_suma:
            producto.cantidad_disponible += cantidad
            producto.cantidad_total += cantidad
        else:
            producto.cantidad_disponible -= cantidad
            producto.cantidad_total -= cantidad
        session.add(producto)
        session.commit()
        session.refresh(producto)
    return producto


# -----------------------------------------------------------------------------
# ROL
# -----------------------------------------------------------------------------
def create_rol(*, session: Session, rol_in: RolCreate) -> Rol:
    """Crear un nuevo rol."""
    db_obj = Rol.model_validate(rol_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_rol(*, session: Session, rol_id: int) -> Rol | None:
    """Obtener un rol por ID."""
    statement = select(Rol).where(Rol.id_rol == rol_id)
    return session.exec(statement).first()


def get_rol_by_nombre(*, session: Session, nombre_rol: str) -> Rol | None:
    """Obtener un rol por nombre."""
    statement = select(Rol).where(Rol.nombre_rol == nombre_rol)
    return session.exec(statement).first()


def get_roles(*, session: Session, skip: int = 0, limit: int = 100) -> list[Rol]:
    """Obtener lista de roles con paginación."""
    statement = select(Rol).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_rol(*, session: Session, db_rol: Rol, rol_in: RolUpdate) -> Rol:
    """Actualizar un rol existente."""
    rol_data = rol_in.model_dump(exclude_unset=True)
    db_rol.sqlmodel_update(rol_data)
    session.add(db_rol)
    session.commit()
    session.refresh(db_rol)
    return db_rol


# -----------------------------------------------------------------------------
# FUNCIONES ADICIONALES PARA USER EN SISTEMA FARMACÉUTICO
# -----------------------------------------------------------------------------
def get_users_by_sucursal(
    *, session: Session, sucursal_id: int, skip: int = 0, limit: int = 100
) -> list[User]:
    """Obtener usuarios de una sucursal específica."""
    statement = (
        select(User)
        .where(User.id_sucursal == sucursal_id)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_users_by_rol(
    *, session: Session, rol_id: int, skip: int = 0, limit: int = 100
) -> list[User]:
    """Obtener usuarios con un rol específico."""
    statement = (
        select(User).where(User.id_rol == rol_id).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


# -----------------------------------------------------------------------------
# MOVIMIENTO INVENTARIO
# -----------------------------------------------------------------------------
def create_movimiento_inventario(
    *, session: Session, movimiento_in: MovimientoInventarioCreate
) -> MovimientoInventario:
    """Crear un nuevo movimiento de inventario."""
    db_obj = MovimientoInventario.model_validate(movimiento_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_movimiento_inventario(
    *, session: Session, movimiento_id: int
) -> MovimientoInventario | None:
    """Obtener un movimiento por ID."""
    statement = select(MovimientoInventario).where(
        MovimientoInventario.id_movimiento == movimiento_id
    )
    return session.exec(statement).first()


def get_movimientos_inventario(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[MovimientoInventario]:
    """Obtener lista de movimientos con paginación."""
    statement = select(MovimientoInventario).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_movimientos_by_producto(
    *, session: Session, producto_id: int, skip: int = 0, limit: int = 100
) -> list[MovimientoInventario]:
    """Obtener movimientos de un producto específico."""
    statement = (
        select(MovimientoInventario)
        .where(MovimientoInventario.id_producto == producto_id)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_movimientos_by_usuario(
    *, session: Session, usuario_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[MovimientoInventario]:
    """Obtener movimientos realizados por un usuario específico."""
    statement = (
        select(MovimientoInventario)
        .where(MovimientoInventario.id_usuario == usuario_id)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_movimientos_by_tipo(
    *, session: Session, tipo: str, skip: int = 0, limit: int = 100
) -> list[MovimientoInventario]:
    """Obtener movimientos por tipo (Entrada, Salida, Transferencia, etc)."""
    statement = (
        select(MovimientoInventario)
        .where(MovimientoInventario.tipo_movimiento == tipo)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def update_movimiento_inventario(
    *,
    session: Session,
    db_movimiento: MovimientoInventario,
    movimiento_in: MovimientoInventarioUpdate,
) -> MovimientoInventario:
    """Actualizar un movimiento existente."""
    movimiento_data = movimiento_in.model_dump(exclude_unset=True)
    db_movimiento.sqlmodel_update(movimiento_data)
    session.add(db_movimiento)
    session.commit()
    session.refresh(db_movimiento)
    return db_movimiento


# -----------------------------------------------------------------------------
# AUDITORIA
# -----------------------------------------------------------------------------
def create_auditoria(*, session: Session, auditoria_in: AuditoriaCreate) -> Auditoria:
    """Crear un nuevo registro de auditoría."""
    db_obj = Auditoria.model_validate(auditoria_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_auditoria(*, session: Session, auditoria_id: int) -> Auditoria | None:
    """Obtener un registro de auditoría por ID."""
    statement = select(Auditoria).where(Auditoria.id_auditoria == auditoria_id)
    return session.exec(statement).first()


def get_auditorias(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[Auditoria]:
    """Obtener lista de auditorías con paginación."""
    statement = select(Auditoria).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_auditorias_by_usuario(
    *, session: Session, usuario_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Auditoria]:
    """Obtener auditorías de un usuario específico."""
    statement = (
        select(Auditoria)
        .where(Auditoria.id_usuario == usuario_id)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_auditorias_by_entidad(
    *, session: Session, entidad: str, skip: int = 0, limit: int = 100
) -> list[Auditoria]:
    """Obtener auditorías de una entidad específica."""
    statement = (
        select(Auditoria)
        .where(Auditoria.entidad_afectada == entidad)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_auditorias_by_registro(
    *, session: Session, entidad: str, registro_id: str, skip: int = 0, limit: int = 100
) -> list[Auditoria]:
    """Obtener auditorías de un registro específico."""
    statement = (
        select(Auditoria)
        .where(Auditoria.entidad_afectada == entidad)
        .where(Auditoria.id_registro_afectado == registro_id)
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())
