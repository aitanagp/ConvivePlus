import json
from fastapi import APIRouter, status, HTTPException, Depends, UploadFile, File
from typing import List

from app.models import StudentIn, StudentDb, StudentOut, StudentImportJson, UserDb
from app.database import get_all_students_db, insert_student, get_student_id_by_email
from app.auth.auth import oauth2_scheme, decode_token
from app.dependencies import get_current_admin, get_current_user

router = APIRouter(prefix="/v1/students", tags=["Students"])

# VER TODOS LOS ALUMNOS
@router.get("/", response_model=List[StudentOut], status_code=status.HTTP_200_OK)
async def get_all_students(current_user: UserDb = Depends(get_current_user)):
    # Obtenemos los alumnos desde la base de datos real
    students_data = get_all_students_db()
    
    # Convertimos los diccionarios a objetos Pydantic StudentOut
    return [StudentOut(**student) for student in students_data]

# CREAR UN ALUMNO (Manual)
@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(student_in: StudentIn, current_user: UserDb = Depends(get_current_admin)):
    new_student = StudentDb(
        name=student_in.name,
        surname=student_in.surname,
        email=student_in.email,
        age=student_in.age,
        student_group=student_in.student_group
    )
    
    student_id = insert_student(new_student)
    if not student_id:
        raise HTTPException(status_code=500, detail="Error al insertar alumno")

    # Devolvemos el objeto con el ID generado
    new_student.id = student_id
    return new_student

# IMPORTAR ALUMNOS DESDE JSON
@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_students_json(
    file: UploadFile = File(...),
    current_user: UserDb = Depends(get_current_admin) # Solo admin puede importar
):
    # Validar extensión
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="El archivo debe ser .json")

    # Leer contenido
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON mal formado")

    created_count = 0
    errors = []

    # Recorrer la lista
    for item in data:
        try:
            # Validamos esquema con el modelo que acabamos de añadir
            student_data = StudentImportJson(**item) 
        except Exception as e:
            errors.append(f"Fila inválida: {item} - Error: {e}")
            continue

        # Comprobar si ya existe el email
        if get_student_id_by_email(student_data.email):
            errors.append(f"Alumno {student_data.email} ya existe")
            continue

        # Preparar objeto para BD
        new_student = StudentDb(
            name=student_data.name,
            surname=student_data.surname,
            email=student_data.email,
            age=student_data.age,
            student_group=student_data.student_group
        )

        # Insertar
        if insert_student(new_student):
            created_count += 1
        else:
            errors.append(f"Error BD al insertar: {student_data.email}")

    return {
        "message": "Importación de alumnos finalizada",
        "alumnos_creados": created_count,
        "errores": errors
    }