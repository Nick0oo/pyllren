import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from sqlmodel import col, delete, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
    get_current_admin_user,
)
from app.core.config import settings
from app.core.cache import (
    get_cache, set_cache, invalidate_entity_cache,
    list_cache_key, item_cache_key
)
from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    Message,
    Rol,
    UpdatePassword,
    User,
    UserCreate,
    UserCreateByAdmin,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services.email_service import send_email_safely
from app.utils import generate_new_account_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_admin_user)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    # Generate cache key
    cache_key = list_cache_key("users", skip=skip, limit=limit)
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return UsersPublic(**cached_result)

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    result = UsersPublic(data=users, count=count)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, result.model_dump(), ttl=300)

    return result


@router.post(
    "/", dependencies=[Depends(get_current_admin_user)], response_model=UserPublic
)
def create_user(
    *, session: SessionDep, user_in: UserCreate, background_tasks: BackgroundTasks
) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        # Enviar email en segundo plano usando BackgroundTask
        # Esto no bloquea la creación del usuario si falla el envío
        background_tasks.add_task(
            send_email_safely,
            to_email=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    
    # Invalidate cache
    invalidate_entity_cache("users")
    
    return user


@router.post(
    "/create-with-role",
    dependencies=[Depends(get_current_admin_user)],
    response_model=UserPublic
)
def create_user_by_admin(*, session: SessionDep, user_in: UserCreateByAdmin) -> Any:
    """
    Crear un nuevo usuario asignando un rol (Farmacéutico, Auxiliar o Auditor) y opcionalmente una sucursal.
    Solo accesible para administradores.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    try:
        user = crud.create_user_by_admin(session=session, user_in=user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    
    # Invalidate cache
    invalidate_entity_cache("users")
    
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    # Invalidate cache for this specific user
    invalidate_entity_cache("users")
    
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    # Generate cache key for current user
    cache_key = item_cache_key("users", str(current_user.id))
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return UserPublic(**cached_result)
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, current_user.model_dump(), ttl=300)
    
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    Asigna automáticamente el rol de Administrador.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    # Obtener el rol de Administrador
    admin_rol = session.exec(
        select(Rol).where(Rol.nombre_rol == "Administrador")
    ).first()
    
    if not admin_rol:
        raise HTTPException(
            status_code=500,
            detail="No se encontró el rol de Administrador en el sistema",
        )
    
    # Crear el usuario con el rol de Administrador
    user_create = UserCreate.model_validate(user_in)
    user_data = user_create.model_dump(exclude_unset=True, exclude={"password"})
    user_data["id_rol"] = admin_rol.id_rol
    user_data["hashed_password"] = get_password_hash(user_in.password)
    
    db_obj = User(**user_data)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    
    return db_obj


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    # Generate cache key
    cache_key = item_cache_key("users", str(user_id))
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return UserPublic(**cached_result)
    
    user = session.get(User, user_id)
    if user == current_user:
        # Cache the result (TTL: 5 minutes)
        set_cache(cache_key, user.model_dump(), ttl=300)
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    
    # Cache the result (TTL: 5 minutes)
    set_cache(cache_key, user.model_dump(), ttl=300)
    
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_admin_user)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    
    # Invalidate cache
    invalidate_entity_cache("users")
    
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_admin_user)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    statement = delete(Item).where(col(Item.owner_id) == user_id)
    session.exec(statement)  # type: ignore
    session.delete(user)
    session.commit()
    
    # Invalidate cache
    invalidate_entity_cache("users")
    
    return Message(message="User deleted successfully")
