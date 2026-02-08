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
    insert_teacher_link
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
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

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

        if not email or not nombre or not contrasena:
            continue

        if get_user_by_username(email):
            errors.append(f"Usuario {email} ya existe")
            continue 

        hashed_pass = get_hash_password(contrasena)
        new_teacher = UserDb(
            username=email, name=nombre, password=hashed_pass, role="TEACHER"
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
