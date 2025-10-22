import uuid
from datetime import date, datetime
from typing import Any

from pydantic import EmailStr
from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
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
    nombre: str = Field(max_length=255)
    direccion: str = Field(max_length=500)
    telefono: str = Field(max_length=50)
    ciudad: str = Field(max_length=100)
    estado: bool = True


class SucursalCreate(SucursalBase):
    pass


class SucursalUpdate(SQLModel):
    nombre: str | None = Field(default=None, max_length=255)
    direccion: str | None = Field(default=None, max_length=500)
    telefono: str | None = Field(default=None, max_length=50)
    ciudad: str | None = Field(default=None, max_length=100)
    estado: bool | None = None


class Sucursal(SucursalBase, table=True):
    id_sucursal: int | None = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    bodegas: list["Bodega"] = Relationship(back_populates="sucursal")
    usuarios: list["Usuario"] = Relationship(back_populates="sucursal")
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
    nombre: str = Field(max_length=255)
    descripcion: str | None = Field(default=None, max_length=500)
    tipo: str = Field(max_length=50)  # Principal, Secundaria, De tránsito
    estado: bool = True


class BodegaCreate(BodegaBase):
    id_sucursal: int


class BodegaUpdate(SQLModel):
    nombre: str | None = Field(default=None, max_length=255)
    descripcion: str | None = Field(default=None, max_length=500)
    tipo: str | None = Field(default=None, max_length=50)
    estado: bool | None = None
    id_sucursal: int | None = None


class Bodega(BodegaBase, table=True):
    id_bodega: int | None = Field(default=None, primary_key=True)
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
    nombre: str = Field(max_length=255)
    nit: str = Field(max_length=50)
    telefono: str = Field(max_length=50)
    email: str = Field(max_length=255)
    direccion: str = Field(max_length=500)
    ciudad: str = Field(max_length=100)
    estado: bool = True


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorUpdate(SQLModel):
    nombre: str | None = Field(default=None, max_length=255)
    nit: str | None = Field(default=None, max_length=50)
    telefono: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    direccion: str | None = Field(default=None, max_length=500)
    ciudad: str | None = Field(default=None, max_length=100)
    estado: bool | None = None


class Proveedor(ProveedorBase, table=True):
    id_proveedor: int | None = Field(default=None, primary_key=True)
    
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
    numero_lote: str = Field(max_length=100)
    fecha_fabricacion: date
    fecha_vencimiento: date
    estado: str = Field(max_length=50)  # Activo, Vencido, Devuelto, En tránsito
    observaciones: str | None = Field(default=None, max_length=1000)


class LoteCreate(LoteBase):
    id_proveedor: int
    id_bodega: int


class LoteUpdate(SQLModel):
    numero_lote: str | None = Field(default=None, max_length=100)
    fecha_fabricacion: date | None = None
    fecha_vencimiento: date | None = None
    id_proveedor: int | None = None
    id_bodega: int | None = None
    estado: str | None = Field(default=None, max_length=50)
    observaciones: str | None = Field(default=None, max_length=1000)


class Lote(LoteBase, table=True):
    id_lote: int | None = Field(default=None, primary_key=True)
    id_proveedor: int = Field(foreign_key="proveedor.id_proveedor")
    id_bodega: int = Field(foreign_key="bodega.id_bodega")
    fecha_registro: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    proveedor: Proveedor | None = Relationship(back_populates="lotes")
    bodega: Bodega | None = Relationship(back_populates="lotes")
    productos: list["Producto"] = Relationship(back_populates="lote")


class LotePublic(LoteBase):
    id_lote: int
    id_proveedor: int
    id_bodega: int
    fecha_registro: datetime


class LotesPublic(SQLModel):
    data: list[LotePublic]
    count: int


# -----------------------------------------------------------------------------
# PRODUCTO
# -----------------------------------------------------------------------------
class ProductoBase(SQLModel):
    nombre_comercial: str = Field(max_length=255)
    nombre_generico: str = Field(max_length=255)
    codigo_interno: str = Field(max_length=100)
    codigo_barras: str = Field(max_length=100)
    forma_farmaceutica: str = Field(max_length=100)
    concentracion: str = Field(max_length=100)
    presentacion: str = Field(max_length=100)
    unidad_medida: str = Field(max_length=50)
    cantidad_total: int
    cantidad_disponible: int
    stock_minimo: int
    stock_maximo: int
    estado: bool = True


class ProductoCreate(ProductoBase):
    id_lote: int


class ProductoUpdate(SQLModel):
    nombre_comercial: str | None = Field(default=None, max_length=255)
    nombre_generico: str | None = Field(default=None, max_length=255)
    codigo_interno: str | None = Field(default=None, max_length=100)
    codigo_barras: str | None = Field(default=None, max_length=100)
    forma_farmaceutica: str | None = Field(default=None, max_length=100)
    concentracion: str | None = Field(default=None, max_length=100)
    presentacion: str | None = Field(default=None, max_length=100)
    unidad_medida: str | None = Field(default=None, max_length=50)
    cantidad_total: int | None = None
    cantidad_disponible: int | None = None
    stock_minimo: int | None = None
    stock_maximo: int | None = None
    id_lote: int | None = None
    estado: bool | None = None


class Producto(ProductoBase, table=True):
    id_producto: int | None = Field(default=None, primary_key=True)
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
    nombre_rol: str = Field(max_length=50)  # Administrador, Farmacéutico, Auxiliar, Auditor
    descripcion: str | None = Field(default=None, max_length=500)
    permisos: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class RolCreate(RolBase):
    pass


class RolUpdate(SQLModel):
    nombre_rol: str | None = Field(default=None, max_length=50)
    descripcion: str | None = Field(default=None, max_length=500)
    permisos: dict[str, Any] | None = None


class Rol(RolBase, table=True):
    id_rol: int | None = Field(default=None, primary_key=True)
    
    # Relaciones
    usuarios: list["Usuario"] = Relationship(back_populates="rol")


class RolPublic(RolBase):
    id_rol: int


class RolesPublic(SQLModel):
    data: list[RolPublic]
    count: int


# -----------------------------------------------------------------------------
# USUARIO (Extendido del sistema farmacéutico)
# -----------------------------------------------------------------------------
class UsuarioBase(SQLModel):
    nombre_completo: str = Field(max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=8, max_length=40)
    id_sucursal: int
    id_rol: int


class UsuarioUpdate(SQLModel):
    nombre_completo: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)
    id_sucursal: int | None = None
    id_rol: int | None = None
    activo: bool | None = None


class Usuario(UsuarioBase, table=True):
    id_usuario: int | None = Field(default=None, primary_key=True)
    id_sucursal: int = Field(foreign_key="sucursal.id_sucursal")
    id_rol: int = Field(foreign_key="rol.id_rol")
    hash_password: str
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    sucursal: Sucursal | None = Relationship(back_populates="usuarios")
    rol: Rol | None = Relationship(back_populates="usuarios")
    movimientos: list["MovimientoInventario"] = Relationship(back_populates="usuario")
    auditorias: list["Auditoria"] = Relationship(back_populates="usuario")


class UsuarioPublic(UsuarioBase):
    id_usuario: int
    id_sucursal: int
    id_rol: int
    fecha_creacion: datetime


class UsuariosPublic(SQLModel):
    data: list[UsuarioPublic]
    count: int


# -----------------------------------------------------------------------------
# MOVIMIENTO INVENTARIO
# -----------------------------------------------------------------------------
class MovimientoInventarioBase(SQLModel):
    tipo_movimiento: str = Field(max_length=50)  # Entrada, Salida, Transferencia, Devolución, Ajuste
    cantidad: int
    descripcion: str | None = Field(default=None, max_length=1000)


class MovimientoInventarioCreate(MovimientoInventarioBase):
    id_producto: int
    id_usuario: int
    id_sucursal_origen: int | None = None
    id_sucursal_destino: int | None = None


class MovimientoInventarioUpdate(SQLModel):
    tipo_movimiento: str | None = Field(default=None, max_length=50)
    cantidad: int | None = None
    id_producto: int | None = None
    id_usuario: int | None = None
    id_sucursal_origen: int | None = None
    id_sucursal_destino: int | None = None
    descripcion: str | None = Field(default=None, max_length=1000)


class MovimientoInventario(MovimientoInventarioBase, table=True):
    id_movimiento: int | None = Field(default=None, primary_key=True)
    id_producto: int = Field(foreign_key="producto.id_producto")
    id_usuario: int = Field(foreign_key="usuario.id_usuario")
    id_sucursal_origen: int | None = Field(default=None, foreign_key="sucursal.id_sucursal")
    id_sucursal_destino: int | None = Field(default=None, foreign_key="sucursal.id_sucursal")
    fecha_movimiento: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    producto: Producto | None = Relationship(back_populates="movimientos")
    usuario: Usuario | None = Relationship(back_populates="movimientos")
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
    id_usuario: int
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
    entidad_afectada: str = Field(max_length=100)
    id_registro_afectado: int
    accion: str = Field(max_length=100)
    detalle: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    resultado: str = Field(max_length=50)  # Éxito, Error


class AuditoriaCreate(AuditoriaBase):
    id_usuario: int


class AuditoriaUpdate(SQLModel):
    entidad_afectada: str | None = Field(default=None, max_length=100)
    id_registro_afectado: int | None = None
    accion: str | None = Field(default=None, max_length=100)
    id_usuario: int | None = None
    detalle: dict[str, Any] | None = None
    resultado: str | None = Field(default=None, max_length=50)


class Auditoria(AuditoriaBase, table=True):
    id_auditoria: int | None = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")
    fecha_accion: datetime = Field(default_factory=datetime.now)
    
    # Relaciones
    usuario: Usuario | None = Relationship(back_populates="auditorias")


class AuditoriaPublic(AuditoriaBase):
    id_auditoria: int
    id_usuario: int
    fecha_accion: datetime


class AuditoriasPublic(SQLModel):
    data: list[AuditoriaPublic]
    count: int


# =============================================================================
# FIN MODELOS DEL SISTEMA DE INVENTARIO FARMACÉUTICO
# =============================================================================


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
