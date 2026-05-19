import json
from fastapi import APIRouter, status, HTTPException, Depends, UploadFile, File
from typing import List

from app.models import StudentIn, StudentDb, StudentOut, StudentImportJson, UserDb, StudentUpdate
from app.database import (
    get_all_students_db, 
    insert_student, 
    get_student_id_by_email,
    get_student_by_id_db,
    update_student_db,
    delete_student_db
)
from app.auth.auth import oauth2_scheme, decode_token
from app.dependencies import get_current_admin, get_current_user

router = APIRouter(prefix="/v1/students", tags=["Students"])

# VER TODOS LOS ALUMNOS
@router.get("/", response_model=List[StudentOut], status_code=status.HTTP_200_OK)
async def get_all_students(
    student_group: str = None,
    current_user: UserDb = Depends(get_current_user)
):
    # Obtenemos los alumnos desde la base de datos real
    students_data = get_all_students_db(student_group=student_group)
    
    # Convertimos los diccionarios a objetos Pydantic StudentOut
    return [StudentOut(**student) for student in students_data]

# VER LA FICHA DE UN ALUMNO
@router.get("/{id}", response_model=StudentOut, status_code=status.HTTP_200_OK)
async def get_student(id: int, current_user: UserDb = Depends(get_current_user)):
    # Busco al alumno por su id en la base de datos
    student = get_student_by_id_db(id)
    if not student:
        # Si no está, mando un error 404 de que no se encuentra
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return student

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

# EDITAR UN ALUMNO
@router.put("/{id}", response_model=StudentOut, status_code=status.HTTP_200_OK)
async def update_student(id: int, student_update: StudentUpdate, current_user: UserDb = Depends(get_current_user)):
    # Solo pueden editar Admin (ROOT) o Dirección (DIRECTOR)
    if current_user.role != 'ROOT' and current_user.role != 'DIRECTOR':
        raise HTTPException(status_code=403, detail="No tienes permiso para editar alumnos.")

    # Intento actualizar en la base de datos
    success = update_student_db(id, student_update)
    if not success:
        raise HTTPException(status_code=404, detail="No se ha podido actualizar, igual el alumno no existe")
    
    # Traigo los datos nuevos para devolverlos
    updated_student = get_student_by_id_db(id)
    return updated_student

# BORRAR UN ALUMNO (Baja)
@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_student(id: int, current_user: UserDb = Depends(get_current_user)):
    # Solo el admin o el dire pueden borrar a alguien
    if current_user.role != 'ROOT' and current_user.role != 'DIRECTOR':
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar alumnos.")

    # Miro si existe antes de intentar borrar
    if not get_student_by_id_db(id):
        raise HTTPException(status_code=404, detail="Ese alumno no esta en la base de datos")

    # Borro de la base de datos (esta función ya limpia las actitudes)
    if delete_student_db(id):
        return {"message": f"Alumno con ID {id} borrado correctamente. Hasta luego!"}
    else:
        raise HTTPException(status_code=500, detail="Algo ha fallado al borrar al alumno en la DB")

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