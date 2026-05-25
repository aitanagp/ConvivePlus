from fastapi import APIRouter, status, HTTPException, Depends
from typing import List, Optional
from datetime import date, time

from app.models import ClassroomAssignmentIn, ClassroomTaskIn, AttendanceUpdate, UserDb
from app.database import (
    insert_classroom_assignment,
    get_daily_classroom_students,
    insert_classroom_task,
    update_classroom_attendance,
    get_student_tasks_report,
    update_classroom_task_status_db
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/v1/classroom", tags=["Classroom"])

# ASIGNAR UN ALUMNO AL AULA
@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def create_assignment(assignment: ClassroomAssignmentIn, current_user: UserDb = Depends(get_current_user)):
    # Solo pueden el admin, director o profes
    if current_user.role not in ['ROOT', 'DIRECTOR', 'TEACHER']:
        raise HTTPException(status_code=403, detail="No tienes permiso para meter a nadie en el aula")

    # Intento guardarlo
    new_id = insert_classroom_assignment(assignment, current_user.id)
    if not new_id:
        # Si devuelve None es que se pisa con otro horario
        raise HTTPException(status_code=400, detail="El alumno ya tiene otra cosa asignada en ese horario o error en los datos")
    
    return {"message": "Asignación creada correctamente", "id": new_id}

# LISTADO DE ALUMNOS DE HOY
@router.get("/daily", status_code=status.HTTP_200_OK)
async def get_daily_students(
    day: Optional[date] = None, 
    current_time: Optional[time] = None,
    current_user: UserDb = Depends(get_current_user)
):
    # Si no me pasan el día uso el de hoy
    target_day = day if day else date.today()
    
    # Saco los alumnos que tienen que estar
    students = get_daily_classroom_students(target_day, current_time)
    return students

# ASIGNAR TAREAS A UN ALUMNO
@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(task: ClassroomTaskIn, current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ['ROOT', 'DIRECTOR', 'TEACHER']:
        raise HTTPException(status_code=403, detail="No puedes poner tareas")

    task_id = insert_classroom_task(task)
    if not task_id:
        raise HTTPException(status_code=500, detail="No se ha podido crear la tarea")
    
    return {"message": "Tarea asignada", "id": task_id}

# PASAR LISTA (ASISTENCIA)
@router.patch("/attendance", status_code=status.HTTP_200_OK)
async def update_attendance(attendance: AttendanceUpdate, current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ['ROOT', 'DIRECTOR', 'TEACHER']:
        raise HTTPException(status_code=403, detail="No puedes pasar lista")

    if update_classroom_attendance(attendance):
        return {"message": "Asistencia registrada"}
    else:
        raise HTTPException(status_code=500, detail="Error al guardar la asistencia")

# REPORTE DE TAREAS PARA EL TUTOR
@router.get("/report/{assignment_id}", status_code=status.HTTP_200_OK)
async def get_report(assignment_id: int, current_user: UserDb = Depends(get_current_user)):
    # Cualquiera logueado puede ver el reporte para informar
    tasks = get_student_tasks_report(assignment_id)
    if not tasks:
        return {"message": "No hay tareas registradas para esta asignación", "tasks": []}
    
    return {
        "assignment_id": assignment_id,
        "tasks": tasks,
        "completed_count": len([t for t in tasks if t["status"] == "COMPLETED"]),
        "total_count": len(tasks)
    }

# ACTUALIZAR ESTADO DE UNA TAREA
@router.patch("/tasks/{task_id}/status", status_code=status.HTTP_200_OK)
async def update_task_status(task_id: int, status_update: dict, current_user: UserDb = Depends(get_current_user)):
    if current_user.role not in ['ROOT', 'DIRECTOR', 'TEACHER']:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar tareas")
    
    status_val = status_update.get("status")
    if not status_val or status_val not in ["PENDING", "COMPLETED"]:
        raise HTTPException(status_code=400, detail="Estado no válido. Debe ser PENDING o COMPLETED")
    
    if update_classroom_task_status_db(task_id, status_val):
        return {"message": "Estado de la tarea actualizado"}
    else:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
