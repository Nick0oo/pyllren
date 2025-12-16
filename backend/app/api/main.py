from fastapi import APIRouter

from app.api.routes import (
    auditorias,
    bodegas,
    items,
    lotes,
    login,
    movimientos,
    notifications,
    private,
    productos,
    proveedores,
    roles,
    sucursales,
    transferencias,
    websockets,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()

# Rutas de autenticación y utilidades
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)

# Rutas del sistema de inventario farmacéutico
api_router.include_router(sucursales.router)
api_router.include_router(bodegas.router)
api_router.include_router(proveedores.router)
api_router.include_router(lotes.router)
api_router.include_router(productos.router)
api_router.include_router(roles.router)
api_router.include_router(movimientos.router)
api_router.include_router(transferencias.router)
api_router.include_router(auditorias.router)
api_router.include_router(notifications.router)
api_router.include_router(websockets.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
