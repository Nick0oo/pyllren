from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep, get_current_admin_user
from app.models import (
    Message,
    Proveedor,
    ProveedorCreate,
    ProveedorPublic,
    ProveedoresPublic,
    ProveedorUpdate,
)

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.get(
    "/",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedoresPublic
)
def read_proveedores(
    session: SessionDep, 
    current_user: CurrentUser, 
    skip: int = 0, 
    limit: int = 100,
    q: str | None = None,
    estado: bool | None = None
) -> Any:
    """
    Retrieve proveedores with optional search and filter.
    """
    # Construir query base
    statement = select(Proveedor)
    count_statement = select(func.count()).select_from(Proveedor)
    
    # Aplicar filtros
    filters = []
    
    if q:
        search_filter = or_(
            Proveedor.nombre.ilike(f"%{q}%"),
            Proveedor.nit.ilike(f"%{q}%"),
            Proveedor.email.ilike(f"%{q}%"),
            Proveedor.telefono.ilike(f"%{q}%")
        )
        filters.append(search_filter)
    
    if estado is not None:
        filters.append(Proveedor.estado == estado)
    
    # Aplicar filtros a ambas queries
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    
    # Ejecutar queries
    count = session.exec(count_statement).one()
    statement = statement.offset(skip).limit(limit)
    proveedores = session.exec(statement).all()
    
    return ProveedoresPublic(data=proveedores, count=count)


@router.get(
    "/stats",
    dependencies=[Depends(get_current_admin_user)]
)
def get_proveedores_stats(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get proveedores statistics.
    """
    # Total proveedores
    total_proveedores = session.exec(select(func.count()).select_from(Proveedor)).one()
    
    # Proveedores activos
    activos = session.exec(
        select(func.count()).select_from(Proveedor).where(Proveedor.estado == True)
    ).one()
    
    # Proveedores inactivos
    inactivos = session.exec(
        select(func.count()).select_from(Proveedor).where(Proveedor.estado == False)
    ).one()
    
    # Total lotes asociados (necesitamos importar Lote)
    from app.models import Lote
    total_lotes = session.exec(
        select(func.count()).select_from(Lote)
    ).one()
    
    return {
        "total_proveedores": total_proveedores,
        "activos": activos,
        "inactivos": inactivos,
        "total_lotes": total_lotes
    }


@router.get(
    "/{id}",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedorPublic
)
def read_proveedor(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get proveedor by ID.
    """
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    return proveedor


@router.post(
    "/",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedorPublic
)
def create_proveedor(
    *, session: SessionDep, current_user: CurrentUser, proveedor_in: ProveedorCreate
) -> Any:
    """
    Create new proveedor.
    """
    # Verificar que el NIT no esté duplicado
    existing_proveedor = session.exec(
        select(Proveedor).where(Proveedor.nit == proveedor_in.nit)
    ).first()
    
    if existing_proveedor:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe un proveedor con el NIT {proveedor_in.nit}"
        )
    
    proveedor = Proveedor.model_validate(proveedor_in)
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor


@router.put(
    "/{id}",
    dependencies=[Depends(get_current_admin_user)],
    response_model=ProveedorPublic
)
def update_proveedor(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    proveedor_in: ProveedorUpdate,
) -> Any:
    """
    Update a proveedor.
    """
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    
    # Si se está actualizando el NIT, verificar que no esté duplicado
    if proveedor_in.nit and proveedor_in.nit != proveedor.nit:
        existing_proveedor = session.exec(
            select(Proveedor).where(Proveedor.nit == proveedor_in.nit)
        ).first()
        
        if existing_proveedor:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe un proveedor con el NIT {proveedor_in.nit}"
            )
    
    update_dict = proveedor_in.model_dump(exclude_unset=True)
    proveedor.sqlmodel_update(update_dict)
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor


@router.delete(
    "/{id}",
    dependencies=[Depends(get_current_admin_user)]
)
def delete_proveedor(
    session: SessionDep, current_user: CurrentUser, id: int
) -> Message:
    """
    Delete a proveedor (soft delete).
    """
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    proveedor.estado = False
    session.add(proveedor)
    session.commit()
    return Message(message="Proveedor deleted successfully")

