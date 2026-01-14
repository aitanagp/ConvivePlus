import token
from app.auth.auth import (
    create_access_token, 
    Token, 
    verify_password, 
    oauth2_scheme, 
    get_hash_password
)
from app.models import UserIn, UserDb, UserOut, UserCreateJson, UserEditJson
from app.database import (
    get_user_by_username, 
    get_user_by_email,
    get_user_by_id,
    insert_user,
    update_user_db, 
    delete_user_db,
    get_all_users_db
)

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, status, HTTPException, Depends, Query

router = APIRouter(
    prefix="/v1/users",
    tags=["Users"]
)

# --- SIGNUP ---
@router.post("/signup/", status_code=status.HTTP_201_CREATED)
async def create_user(userIn: UserIn):
    # Verificar si existe
    existing_user = get_user_by_username(userIn.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya existe"
        )

    # HASHEAR la contraseña
    hashed_password = get_hash_password(userIn.password)

    # Insertar con la contraseña encriptada
    insert_user(
        UserDb(
            name=userIn.name,
            username=userIn.username,
            password=hashed_password
        )
    )
    return {"msg": "Usuario creado correctamente"}

# --- LOGIN ---
@router.post("/login/", response_model=Token, status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    
    user_db = get_user_by_username(username)
    
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    if not verify_password(password, user_db.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
        
    access_token = create_access_token(
        data={"sub": user_db.username} 
    ) 
        
    return {"access_token": access_token, "token_type": "bearer"}

# --- GET ALL ---
@router.get("/all", response_model=list[UserOut]) 
async def get_all_users(token: str = Depends(oauth2_scheme)):
    # Llamamos a la base de datos real
    users = get_all_users_db() 
    
    # Convertimos los resultados al modelo de salida (sin contraseñas)
    return [
        UserOut(id=u.id, name=u.name, username=u.username) for u in users
    ]

# --- FIND (Buscar por email - Admin) ---
@router.get("/find", status_code=status.HTTP_200_OK)
async def get_user_admin(
    email: str = Query(...), 
    token: str = Depends(oauth2_scheme)
):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# --- CREATE (Crear Admin manual) ---
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserCreateJson, 
    token: str = Depends(oauth2_scheme)
):
    existe = get_user_by_email(user_data.email)
    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya existe"
        )
        
    # HASHEAR PASSWORD AQUÍ TAMBIÉN
    hashed_password = get_hash_password(user_data.contrasena)
    
    nuevo_usuario = UserDb(
        id=user_data.id_usuario,
        name=user_data.nombre,
        username=user_data.email, 
        password=hashed_password,
        email=user_data.email
    )
    
    insert_user(nuevo_usuario)
    
    # Devolvemos datos pero borramos la pass de la respuesta por seguridad
    user_data.contrasena = "********"
    return {"mensaje": "Usuario creado", "datos": user_data}

# --- UPDATE ---
@router.put("/", status_code=status.HTTP_200_OK)
async def update_user_admin(
    user_data: UserEditJson,
    id: int = Query(...),
    token: str = Depends(oauth2_scheme)
):
    usuario_actual = get_user_by_id(id)
    if not usuario_actual:
        raise HTTPException(status_code=404, detail="ID no encontrado")
        
    datos_nuevos = {
        "email": user_data.email,
        "name": user_data.nombre
    }
    
    update_user_db(id, datos_nuevos)
    return {"mensaje": "Actualizado correctamente"}

# --- DELETE ---
@router.delete("/", status_code=status.HTTP_200_OK)
async def delete_user_admin(
    id: int = Query(...),
    token: str = Depends(oauth2_scheme)
):
    usuario = get_user_by_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no existe")
        
    delete_user_db(id)
    return {"mensaje": "Usuario eliminado"}