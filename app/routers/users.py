import json
from fastapi import APIRouter, status, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from app.models import (
    UserCreateJson, UserOut, UserDb, Token
)
from app.database import (
    get_user_by_username, 
    insert_user, 
    delete_user_db,
    insert_teacher_link,
    get_all_users_db,
    get_user_by_id,
    update_user_db
)
from app.auth.auth import (
    get_hash_password, 
    verify_password, 
    create_access_token
)
from app.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/v1/users", tags=["Users"])

@router.post("/login/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role, "id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}
    
# CREAR USUARIO (INDIVIDUAL)
from app.models import UserCreate
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, 
    admin_user: UserDb = Depends(get_current_admin)
):
    # Comprobar si ya existe
    if get_user_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    hashed_pass = get_hash_password(user_in.password)
    new_user = UserDb(
        username=user_in.username, 
        name=user_in.name, 
        password=hashed_pass, 
        role=user_in.role,
        department=user_in.department
    )
    
    user_id = insert_user(new_user)
    if user_id == -1:
        raise HTTPException(status_code=500, detail="Error al crear el usuario en la base de datos")
    
    # Si el rol es TEACHER, DIRECTOR o ROOT, vincular en las tablas correspondientes
    if user_in.role in ["TEACHER", "DIRECTOR", "ROOT"]:
        insert_user_role(user_id, user_in.role)
        
    return get_user_by_id(user_id)

# IMPORTAR PROFESORES JSON
@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_teachers_from_json(
    file: UploadFile = File(...),
    admin_user: UserDb = Depends(get_current_admin)
):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un .json")

    content = await file.read()
    try:
        users_list = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON mal formado")

    created_count = 0
    errors = []

    for user_data in users_list:
        email = user_data.get("email")
        nombre = user_data.get("nombre")
        contrasena = user_data.get("contrasena")
        departamento = user_data.get("departamento")

        if not email or not nombre or not contrasena:
            continue

        if get_user_by_username(email):
            errors.append(f"Usuario {email} ya existe")
            continue 

        hashed_pass = get_hash_password(contrasena)
        new_teacher = UserDb(
            username=email, name=nombre, password=hashed_pass, role="TEACHER", department=departamento
        )
        
        # Guardamos en USER
        user_id = insert_user(new_teacher)
        
        if user_id != -1:
            # guardamos en TECHAER
            insert_teacher_link(user_id) 
            created_count += 1
        else:
            errors.append(f"Error BD: {email}")

    return {"message": "Importación finalizada", "creados": created_count, "errores": errors}

# LISTAR TODOS LOS USUARIOS
@router.get("/", response_model=List[UserOut])
async def get_users(admin_user: UserDb = Depends(get_current_admin)):
    users = get_all_users_db()
    return users

# OBTENER UN USUARIO POR ID
@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, current_user: UserDb = Depends(get_current_user)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# ACTUALIZAR USUARIO
from app.models import UserUpdate
@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    admin_user: UserDb = Depends(get_current_admin)
):
    # Comprobar si existe
    existing_user = get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar en BD
    update_user_db(user_id, user_data.dict())
    
    # Devolver el usuario actualizado
    return get_user_by_id(user_id)

# ELIMINAR USUARIO
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, admin_user: UserDb = Depends(get_current_admin)):
    existing_user = get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    delete_user_db(user_id)
    return None
