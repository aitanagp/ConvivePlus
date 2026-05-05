from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.database import (
    init_probi_table, insert_probi_nomination, get_probi_hall_of_fame,
    get_probi_suggestions, delete_probi_recognition
)
from app.dependencies import get_current_user
from app.models import UserDb
import mariadb
from app.database import db_config

router = APIRouter(
    prefix="/v1/probi",
    tags=["Probi"]
)

init_probi_table()

class NominateIn(BaseModel):
    student_id: int
    justification: str

class ProbiOut(BaseModel):
    id: int
    student_name: str
    teacher_name: str
    justification: str
    created_at: str

class SuggestionOut(BaseModel):
    student_id: int
    name: str
    surname: str
    recognitions: int

@router.post("/nominate")
def nominate_student(nomination: NominateIn, current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ["TEACHER", "DIRECTOR", "ROOT"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para nominar alumnos.")
    
    probi_id = insert_probi_nomination(nomination.student_id, current_user.id, nomination.justification)
    
    if current_user.role in ["DIRECTOR", "ROOT"]:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE PROBI_RECOGNITION SET status = 'APPROVED' WHERE id = ?", (probi_id,))
                conn.commit()
    
    return {
        "message": "¡Felicidades! La nominación Probi para el alumno ha sido registrada exitosamente. Un paso más para una mejor convivencia.",
        "probi_id": probi_id,
        "status": "APPROVED" if current_user.role in ["DIRECTOR", "ROOT"] else "PENDING"
    }

@router.get("/hall-of-fame")
def hall_of_fame():
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT p.id, s.name, s.surname, u.name as teacher_name, p.justification, p.created_at
                FROM PROBI_RECOGNITION p
                JOIN STUDENT s ON p.student_id = s.id
                JOIN USER u ON p.teacher_id = u.id
                WHERE p.status = 'APPROVED'
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                {"id": r[0], "student_name": f"{r[1]} {r[2]}", "teacher_name": r[3], "justification": r[4], "created_at": str(r[5])}
                for r in rows
            ]

@router.get("/suggestions", response_model=List[SuggestionOut])
def suggestions():
    return get_probi_suggestions()

@router.delete("/{probi_id}")
def delete_probi(probi_id: int, current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ["DIRECTOR", "ROOT"]:
        raise HTTPException(status_code=403, detail="Solo Dirección puede retirar reconocimientos.")
    
    success = delete_probi_recognition(probi_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reconocimiento no encontrado.")
    return {"message": "Reconocimiento retirado correctamente."}

@router.put("/{probi_id}/approve")
def approve_probi(probi_id: int, current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ["DIRECTOR", "ROOT"]:
        raise HTTPException(status_code=403, detail="Solo Dirección puede validar reconocimientos.")
    
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE PROBI_RECOGNITION SET status = 'APPROVED' WHERE id = ?", (probi_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Reconocimiento no encontrado.")
            conn.commit()
    return {"message": "Reconocimiento aprobado exitosamente."}
