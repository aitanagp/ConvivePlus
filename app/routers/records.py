from fastapi import APIRouter, status, HTTPException, Depends
from typing import List

from app.models import DisciplinaryRecordOpen, DisciplinaryRecordStatusUpdate, UserDb
from app.database import (
    open_disciplinary_record_db,
    get_student_records_db,
    update_record_status_db,
    get_pending_records_db
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/v1/records", tags=["Disciplinary Records"])

# ABRIR UN NUEVO EXPEDIENTE
@router.post("/open", status_code=status.HTTP_201_CREATED)
async def open_record(record_in: DisciplinaryRecordOpen, current_user: UserDb = Depends(get_current_user)):
    # Solo Dirección puede abrir expedientes
    if current_user.role != 'DIRECTOR' and current_user.role != 'ROOT':
        raise HTTPException(status_code=403, detail="Solo Dirección puede abrir expedientes disciplinarios")

    record_id = open_disciplinary_record_db(record_in)
    if not record_id:
        raise HTTPException(status_code=400, detail="No se ha podido abrir el expediente. Comprueba que las amonestaciones sean correctas.")
    
    return {"message": "Expediente abierto correctamente", "id": record_id}

# CONSULTAR HISTORIAL DE UN ALUMNO
@router.get("/{student_id}", status_code=status.HTTP_200_OK)
async def get_student_records(student_id: int, current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ['DIRECTOR', 'ROOT']:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver expedientes")
    
    return get_student_records_db(student_id)

# ACTUALIZAR ESTADO U OBSERVACIONES
@router.put("/{record_id}/status", status_code=status.HTTP_200_OK)
async def update_status(record_id: int, update_data: DisciplinaryRecordStatusUpdate, current_user: UserDb = Depends(get_current_user)):
    if current_user.role != 'DIRECTOR' and current_user.role != 'ROOT':
        raise HTTPException(status_code=403, detail="Solo Dirección puede tramitar expedientes")

    if update_record_status_db(record_id, update_data):
        return {"message": "Estado del expediente actualizado"}
    else:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

# LISTADO DE EXPEDIENTES PENDIENTES
@router.get("/pending/list", status_code=status.HTTP_200_OK) # Pongo list para que no choque con {student_id}
async def get_pending(current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ['DIRECTOR', 'ROOT']:
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    return get_pending_records_db()
