from fastapi import APIRouter, status, HTTPException, Depends
from typing import List

from app.models import AcademicYearIn, AcademicYearOut, UserDb
from app.database import (
    insert_academic_year_db,
    get_academic_years_db,
    set_current_academic_year_db
)
from app.dependencies import get_current_admin # Solo ROOT o admin para esto

router = APIRouter(prefix="/v1/academic-years", tags=["Academic Years"])

# CREAR NUEVO CURSO
@router.post("/", response_model=AcademicYearOut, status_code=status.HTTP_201_CREATED)
async def create_year(year_in: AcademicYearIn, current_user: UserDb = Depends(get_current_admin)):
    # Solo el Superusuario puede hacer esto según RF14
    if current_user.role != 'ROOT':
        raise HTTPException(status_code=403, detail="Solo el Superusuario puede gestionar cursos académicos")

    year_id = insert_academic_year_db(year_in)
    if not year_id:
        raise HTTPException(status_code=400, detail="No se pudo crear el curso")
    
    return {**year_in.dict(), "id": year_id, "is_active": False}

# LISTAR TODOS LOS CURSOS
@router.get("/", response_model=List[AcademicYearOut])
async def list_years(current_user: UserDb = Depends(get_current_admin)):
    return get_academic_years_db()

# ACTIVAR UN CURSO
@router.patch("/{year_id}/set-current", status_code=status.HTTP_200_OK)
async def set_current(year_id: int, current_user: UserDb = Depends(get_current_admin)):
    if current_user.role != 'ROOT':
        raise HTTPException(status_code=403, detail="Solo el Superusuario puede cambiar el curso activo")

    if set_current_academic_year_db(year_id):
        return {"message": "Curso académico activado correctamente"}
    else:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
