from fastapi import APIRouter, status, HTTPException, Depends
from app.auth.auth import oauth2_scheme, decode_token
from app.models import CreateAttitude
from app.database import (
    get_user_by_username,
    get_student_id_by_email,
    insert_attitude 
)

router = APIRouter(
    prefix="/v1/attitudes",
    tags=["Attitudes"]
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    token_data = decode_token(token)
    user = get_user_by_username(token_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Login incorrecto")
    return user


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_attitude(
    datos: CreateAttitude,
    current_user = Depends(get_current_user)
):
    # Buscar el ID del alumno (usando tu función existente)
    student_id = get_student_id_by_email(datos.student_email)
    
    if not student_id:
        raise HTTPException(status_code=404, detail="No encuentro al alumno con ese email")

    # Ver si es Warning o Recognition (Simple)
    # Convertimos a mayúsculas para que coincida con lo que espera la base de datos
    tipo_para_bd = "RECOGNITION" # Por defecto
    
    if "warning" in datos.type.lower() or "amonestacion" in datos.type.lower():
        tipo_para_bd = "WARNING"

    # Llamar a la función de base de datos
    exito = insert_attitude(
        teacher_id=current_user.id,
        student_id=student_id,
        description=datos.motive,
        tipo=tipo_para_bd
    )

    if exito:
        return {"mensaje": "Guardado correctamente", "tipo": tipo_para_bd}
    else:
        raise HTTPException(status_code=500, detail="Error al guardar en la base de datos")