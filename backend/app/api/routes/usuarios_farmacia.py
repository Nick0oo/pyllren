from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.security import get_password_hash
from app.models import (
    Message,
    Usuario,
    UsuarioCreate,
    UsuarioPublic,
    UsuariosPublic,
    UsuarioUpdate,
)

router = APIRouter(prefix="/usuarios-farmacia", tags=["usuarios-farmacia"])


@router.get("/", response_model=UsuariosPublic)
def read_usuarios(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve usuarios.
    """
    count_statement = select(func.count()).select_from(Usuario)
    count = session.exec(count_statement).one()
    statement = select(Usuario).offset(skip).limit(limit)
    usuarios = session.exec(statement).all()
    return UsuariosPublic(data=usuarios, count=count)


@router.get("/{id}", response_model=UsuarioPublic)
def read_usuario(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get usuario by ID.
    """
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return usuario


@router.post("/", response_model=UsuarioPublic)
def create_usuario(
    *, session: SessionDep, current_user: CurrentUser, usuario_in: UsuarioCreate
) -> Any:
    """
    Create new usuario.
    """
    usuario = Usuario.model_validate(
        usuario_in, update={"hash_password": get_password_hash(usuario_in.password)}
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.put("/{id}", response_model=UsuarioPublic)
def update_usuario(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    usuario_in: UsuarioUpdate,
) -> Any:
    """
    Update a usuario.
    """
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
    
    update_dict = usuario_in.model_dump(exclude_unset=True)
    if "password" in update_dict:
        hashed_password = get_password_hash(update_dict["password"])
        del update_dict["password"]
        update_dict["hash_password"] = hashed_password
    
    usuario.sqlmodel_update(update_dict)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.delete("/{id}")
def delete_usuario(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Delete a usuario (soft delete).
    """
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
    usuario.activo = False
    session.add(usuario)
    session.commit()
    return Message(message="Usuario deleted successfully")

