from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth.auth import decode_token, oauth2_scheme
from app.database import get_user_by_username
from app.models import UserDb

async def get_current_user(token: str = Depends(oauth2_scheme)):
    token_data = decode_token(token)
    user = get_user_by_username(token_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_admin(current_user: UserDb = Depends(get_current_user)):
    # Verifica si el rol es admin (ajusta 'admin' si en tu BD se llama 'ROOT' o 'DIRECTOR')
    if current_user.role != 'admin' and current_user.role != 'ROOT': 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de Administrador"
        )
    return current_user