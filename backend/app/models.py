import uuid
from datetime import date, datetime
from typing import Any

from pydantic import EmailStr
from sqlalchemy import CheckConstraint, Column, JSON, String
from sqlmodel import Field, Relationship, SQLModel


# =============================================================================
# MODELO USER - UNIFICADO PARA AUTENTICACIÓN Y SISTEMA FARMACÉUTICO
# =============================================================================

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


class UserCreateByAdmin(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)
    id_sucursal: int | None = Field(default=None, description="ID de la sucursal (opcional)")
    id_rol: int = Field(description="ID del rol: 3=Auxiliar, 4=Auditor")


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    __tablename__ = "user"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    
    # Campos adicionales para el sistema farmacéutico
    id_sucursal: int | None = Field(default=None, foreign_key="sucursal.id_sucursal")
    id_rol: int | None = Field(default=None, foreign_key="rol.id_rol")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    items: list["Item"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
        sa_relationship_kwargs={"lazy": "select"}
    )
    movimientos: list["MovimientoInventario"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "select"}
    )
    auditorias: list["Auditoria"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "select"}
    )
    
    # Relaciones farmacéuticas - omitidas para evitar referencias circulares
    # sucursal y rol se pueden acceder mediante queries explícitas


class UserPublic(UserBase):
    id: uuid.UUID
    id_sucursal: int | None = None
    id_rol: int | None = None
    fecha_creacion: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# =============================================================================
# MODELO ITEM - MANTIENE UUID PARA COMPATIBILIDAD
# =============================================================================

class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# =============================================================================
# MODELOS DEL SISTEMA DE INVENTARIO FARMACÉUTICO
# =============================================================================

# -----------------------------------------------------------------------------
# SUCURSAL
# -----------------------------------------------------------------------------
class SucursalBase(SQLModel):
    nombre: str
    direccion: str
    telefono: str
    ciudad: str
    estado: bool = True


class SucursalCreate(SucursalBase):
    pass


class SucursalUpdate(SQLModel):
    nombre: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    ciudad: str | None = None
    estado: bool | None = None


class Sucursal(SucursalBase, table=True):
    __tablename__ = "sucursal"
    
    id_sucursal: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    bodegas: list["Bodega"] = Relationship(back_populates="sucursal")
    movimientos_origen: list["MovimientoInventario"] = Relationship(
        back_populates="sucursal_origen",
        sa_relationship_kwargs={"foreign_keys": "MovimientoInventario.id_sucursal_origen"}
    )
    movimientos_destino: list["MovimientoInventario"] = Relationship(
        back_populates="sucursal_destino",
        sa_relationship_kwargs={"foreign_keys": "MovimientoInventario.id_sucursal_destino"}
    )


class SucursalPublic(SucursalBase):
    id_sucursal: int
    fecha_creacion: datetime


class SucursalesPublic(SQLModel):
    data: list[SucursalPublic]
    count: int


# -----------------------------------------------------------------------------
# BODEGA
# -----------------------------------------------------------------------------
class BodegaBase(SQLModel):
    nombre: str
    descripcion: str | None = None
    tipo: str  # Principal, Secundaria, De tránsito
    estado: bool = True


class BodegaCreate(BodegaBase):
    id_sucursal: int


class BodegaUpdate(SQLModel):
    nombre: str | None = None
    descripcion: str | None = None
    tipo: str | None = None
    estado: bool | None = None
    id_sucursal: int | None = None


class Bodega(BodegaBase, table=True):
    __tablename__ = "bodega"
    
    id_bodega: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    id_sucursal: int = Field(foreign_key="sucursal.id_sucursal")
    
    # Relaciones
    sucursal: Sucursal | None = Relationship(back_populates="bodegas")
    lotes: list["Lote"] = Relationship(back_populates="bodega")


class BodegaPublic(BodegaBase):
    id_bodega: int
    id_sucursal: int


class BodegasPublic(SQLModel):
    data: list[BodegaPublic]
    count: int


# -----------------------------------------------------------------------------
# PROVEEDOR
# -----------------------------------------------------------------------------
class ProveedorBase(SQLModel):
    nombre: str
    nit: str = Field(unique=True, index=True)
    telefono: str
    email: str
    direccion: str
    ciudad: str
    estado: bool = True


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorUpdate(SQLModel):
    nombre: str | None = None
    nit: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    estado: bool | None = None


class Proveedor(ProveedorBase, table=True):
    __tablename__ = "proveedor"
    
    id_proveedor: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    
    # Relaciones
    lotes: list["Lote"] = Relationship(back_populates="proveedor")


class ProveedorPublic(ProveedorBase):
    id_proveedor: int


class ProveedoresPublic(SQLModel):
    data: list[ProveedorPublic]
    count: int


# -----------------------------------------------------------------------------
# LOTE
# -----------------------------------------------------------------------------
class LoteBase(SQLModel):
    numero_lote: str
    fecha_fabricacion: date
    fecha_vencimiento: date
    estado: str  # Activo, Vencido, Devuelto, En tránsito
    observaciones: str | None = None


class LoteCreate(SQLModel):
    numero_lote: str | None = None  # Opcional, se genera automáticamente si es None
    fecha_fabricacion: date
    fecha_vencimiento: date
    estado: str = "Activo"
    observaciones: str | None = None
    id_proveedor: int
    id_bodega: int | None = None


class LoteUpdate(SQLModel):
    numero_lote: str | None = None
    fecha_fabricacion: date | None = None
    fecha_vencimiento: date | None = None
    id_proveedor: int | None = None
    id_bodega: int | None = None
    estado: str | None = None
    observaciones: str | None = None


class Lote(LoteBase, table=True):
    __tablename__ = "lote"
    
    id_lote: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    id_proveedor: int = Field(foreign_key="proveedor.id_proveedor")
    id_bodega: int | None = Field(default=None, foreign_key="bodega.id_bodega")
    fecha_registro: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    proveedor: Proveedor | None = Relationship(back_populates="lotes")
    bodega: Bodega | None = Relationship(back_populates="lotes")
    productos: list["Producto"] = Relationship(back_populates="lote")


class LotePublic(LoteBase):
    id_lote: int
    id_proveedor: int
    id_bodega: int | None
    fecha_registro: datetime


class LotesPublic(SQLModel):
    data: list[LotePublic]
    count: int


class LoteReciente(SQLModel):
    """Modelo simple para lotes recientes (solo campos esenciales)."""
    id_lote: int
    numero_lote: str
    fecha_registro: datetime


# -----------------------------------------------------------------------------
# PRODUCTO
# -----------------------------------------------------------------------------
class ProductoBase(SQLModel):
    nombre_comercial: str
    nombre_generico: str | None = None
    codigo_interno: str | None = None
    codigo_barras: str | None = None
    forma_farmaceutica: str
    concentracion: str
    presentacion: str
    unidad_medida: str
    cantidad_total: int
    cantidad_disponible: int
    stock_minimo: int
    stock_maximo: int
    estado: bool = True


class ProductoCreate(ProductoBase):
    id_lote: int


class ProductoUpdate(SQLModel):
    nombre_comercial: str | None = None
    nombre_generico: str | None = None
    codigo_interno: str | None = None
    codigo_barras: str | None = None
    forma_farmaceutica: str | None = None
    concentracion: str | None = None
    presentacion: str | None = None
    unidad_medida: str | None = None
    cantidad_total: int | None = None
    cantidad_disponible: int | None = None
    stock_minimo: int | None = None
    stock_maximo: int | None = None
    id_lote: int | None = None
    estado: bool | None = None


class Producto(ProductoBase, table=True):
    __tablename__ = "producto"
    
    id_producto: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    id_lote: int = Field(foreign_key="lote.id_lote")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    lote: Lote | None = Relationship(back_populates="productos")
    movimientos: list["MovimientoInventario"] = Relationship(back_populates="producto")


class ProductoPublic(ProductoBase):
    id_producto: int
    id_lote: int
    fecha_creacion: datetime


class ProductosPublic(SQLModel):
    data: list[ProductoPublic]
    count: int


# -----------------------------------------------------------------------------
# ROL
# -----------------------------------------------------------------------------
class RolBase(SQLModel):
    nombre_rol: str  # Administrador, Farmacéutico, Auxiliar, Auditor
    descripcion: str | None = None
    permisos: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class RolCreate(RolBase):
    pass


class RolUpdate(SQLModel):
    nombre_rol: str | None = None
    descripcion: str | None = None
    permisos: dict[str, Any] | None = None


class Rol(RolBase, table=True):
    __tablename__ = "rol"
    
    id_rol: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    
    # Relaciones (omitted to avoid circular references)


class RolPublic(RolBase):
    id_rol: int


class RolesPublic(SQLModel):
    data: list[RolPublic]
    count: int


# -----------------------------------------------------------------------------
# MOVIMIENTO INVENTARIO
# -----------------------------------------------------------------------------
class MovimientoInventarioBase(SQLModel):
    tipo_movimiento: str  # Entrada, Salida, Transferencia, Devolución, Ajuste
    cantidad: int
    descripcion: str | None = None


class MovimientoInventarioCreate(MovimientoInventarioBase):
    id_producto: int
    id_usuario: str  # UUID de User
    id_sucursal_origen: int | None = None
    id_sucursal_destino: int | None = None


class MovimientoInventarioUpdate(SQLModel):
    tipo_movimiento: str | None = None
    cantidad: int | None = None
    id_producto: int | None = None
    id_usuario: str | None = None
    id_sucursal_origen: int | None = None
    id_sucursal_destino: int | None = None
    descripcion: str | None = None


class MovimientoInventario(MovimientoInventarioBase, table=True):
    __tablename__ = "movimientoinventario"
    
    id_movimiento: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    id_producto: int = Field(foreign_key="producto.id_producto")
    id_usuario: uuid.UUID = Field(foreign_key="user.id")
    id_sucursal_origen: int | None = Field(default=None, foreign_key="sucursal.id_sucursal")
    id_sucursal_destino: int | None = Field(default=None, foreign_key="sucursal.id_sucursal")
    fecha_movimiento: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    producto: Producto | None = Relationship(back_populates="movimientos")
    usuario: User | None = Relationship(back_populates="movimientos")
    sucursal_origen: Sucursal | None = Relationship(
        back_populates="movimientos_origen",
        sa_relationship_kwargs={"foreign_keys": "MovimientoInventario.id_sucursal_origen"}
    )
    sucursal_destino: Sucursal | None = Relationship(
        back_populates="movimientos_destino",
        sa_relationship_kwargs={"foreign_keys": "MovimientoInventario.id_sucursal_destino"}
    )


class MovimientoInventarioPublic(MovimientoInventarioBase):
    id_movimiento: int
    id_producto: int
    id_usuario: uuid.UUID
    id_sucursal_origen: int | None
    id_sucursal_destino: int | None
    fecha_movimiento: datetime


class MovimientosInventarioPublic(SQLModel):
    data: list[MovimientoInventarioPublic]
    count: int


# -----------------------------------------------------------------------------
# AUDITORIA
# -----------------------------------------------------------------------------
class AuditoriaBase(SQLModel):
    entidad_afectada: str
    id_registro_afectado: str  # UUID o int según la entidad
    accion: str
    detalle: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    resultado: str  # Éxito, Error


class AuditoriaCreate(AuditoriaBase):
    id_usuario: str  # UUID de User


class AuditoriaUpdate(SQLModel):
    entidad_afectada: str | None = None
    id_registro_afectado: str | None = None
    accion: str | None = None
    id_usuario: str | None = None
    detalle: dict[str, Any] | None = None
    resultado: str | None = None


class Auditoria(AuditoriaBase, table=True):
    __tablename__ = "auditoria"
    
    id_auditoria: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    id_usuario: uuid.UUID = Field(foreign_key="user.id")
    fecha_accion: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    usuario: User | None = Relationship(back_populates="auditorias")


class AuditoriaPublic(AuditoriaBase):
    id_auditoria: int
    id_usuario: uuid.UUID
    fecha_accion: datetime


class AuditoriasPublic(SQLModel):
    data: list[AuditoriaPublic]
    count: int


# =============================================================================
# MODELOS GENÉRICOS PARA API
# =============================================================================

class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
