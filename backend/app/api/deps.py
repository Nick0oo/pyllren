from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User
from sqlmodel import select
from app.models import Bodega

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_current_admin_user(current_user: CurrentUser) -> User:
    """
    Permite acceso a superusuarios o usuarios con rol Administrador (id_rol = 1)
    """
    if not current_user.is_superuser and current_user.id_rol != 1:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    
    return current_user


# -----------------------------------------------------------------------------
# Helpers de alcance/visibilidad por rol
# -----------------------------------------------------------------------------
def is_admin_user(current_user: CurrentUser) -> bool:
    """Un usuario es admin si es superusuario o tiene rol Administrador (id_rol = 1)."""
    return bool(current_user.is_superuser or current_user.id_rol == 1)


def get_user_scope(current_user: CurrentUser) -> dict | None:
    """
    Retorna None si el usuario es admin (acceso total),
    o un dict con `id_sucursal` para filtrar datos.
    """
    if is_admin_user(current_user):
        return None
    return {"id_sucursal": current_user.id_sucursal}


def ensure_bodega_in_scope(session: SessionDep, bodega_id: int, current_user: CurrentUser) -> None:
    """
    Valida que la bodega pertenezca a la sucursal del usuario cuando no es admin.
    Lanza 404 si la bodega no existe o 403 si está fuera de alcance.
    """
    bodega = session.get(Bodega, bodega_id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega not found")

    if is_admin_user(current_user):
        return

    if current_user.id_sucursal is None or bodega.id_sucursal != current_user.id_sucursal:
        raise HTTPException(status_code=403, detail="Bodega fuera de alcance para el usuario")