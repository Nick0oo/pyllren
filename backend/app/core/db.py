from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Rol, RolCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    # Crear roles si no existen
    roles_to_create = [
        {"nombre_rol": "Administrador", "descripcion": "Acceso completo al sistema", "permisos": {}},
        {"nombre_rol": "Farmacéutico", "descripcion": "Gestión de inventario y productos", "permisos": {}},
        {"nombre_rol": "Auxiliar", "descripcion": "Operaciones básicas del sistema", "permisos": {}},
        {"nombre_rol": "Auditor", "descripcion": "Solo lectura y auditoría", "permisos": {}},
    ]
    
    for rol_data in roles_to_create:
        existing_rol = session.exec(
            select(Rol).where(Rol.nombre_rol == rol_data["nombre_rol"])
        ).first()
        if not existing_rol:
            rol = Rol(**rol_data)
            session.add(rol)
    
    session.commit()
    
    # Obtener el rol de Administrador
    admin_rol = session.exec(
        select(Rol).where(Rol.nombre_rol == "Administrador")
    ).first()

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
        
        # Asignar rol de Administrador al primer usuario
        if admin_rol:
            user.id_rol = admin_rol.id_rol
            session.add(user)
            session.commit()
            session.refresh(user)
