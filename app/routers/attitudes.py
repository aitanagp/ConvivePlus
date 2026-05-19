from fastapi import APIRouter, status, HTTPException, Depends
from app.auth.auth import oauth2_scheme, decode_token
from app.models import CreateAttitude, AttitudeUpdate
from app.database import (
    get_user_by_username,
    get_student_id_by_email,
    insert_attitude,
    get_attitudes_db,
    get_attitude_owner_id,
    update_attitude_db,
    delete_attitude_db
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
    # Buscar el ID del alumno
    student_id = get_student_id_by_email(datos.student_email)
    
    if not student_id:
        raise HTTPException(status_code=404, detail="No encuentro al alumno con ese email")

    # Ver si es Warning o Recognition
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

@router.get("/")
async def list_attitudes(current_user = Depends(get_current_user)):
    # Solo Admin (ROOT) o Direccion pueden ver todas las actitudes de todo el mundo
    if current_user.role not in ["ROOT", "DIRECTOR"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver todas las actitudes")
    
    return get_attitudes_db()

@router.get("/me")
async def list_my_attitudes(current_user = Depends(get_current_user)):
    # Los profes solo ven las suyas
    return get_attitudes_db(teacher_id=current_user.id)

@router.put("/{attitude_id}")
async def update_attitude(
    attitude_id: int, 
    datos: AttitudeUpdate, 
    current_user = Depends(get_current_user)
):
    # Vemos si la actitud existe y quién es el dueño
    owner_id = get_attitude_owner_id(attitude_id)
    if not owner_id:
        raise HTTPException(status_code=404, detail="Esa actitud no existe")
    
    # Solo el creador o root/director pueden editarla
    if owner_id != current_user.id and current_user.role not in ["ROOT", "DIRECTOR"]:
        raise HTTPException(status_code=403, detail="No puedes editar una actitud que no has puesto tú")
    
    update_attitude_db(attitude_id, datos.motive)
    return {"mensaje": "Actitud modificada con éxito"}

@router.delete("/{attitude_id}")
async def delete_attitude(
    attitude_id: int, 
    current_user = Depends(get_current_user)
):
    # Ver si existe
    owner_id = get_attitude_owner_id(attitude_id)
    if not owner_id:
        raise HTTPException(status_code=404, detail="Esa actitud no existe")
    
    # Solo el autor o root/director pueden borrar
    if owner_id != current_user.id and current_user.role not in ["ROOT", "DIRECTOR"]:
        raise HTTPException(status_code=403, detail="No puedes borrar esto, no eres el autor")
    
    delete_attitude_db(attitude_id)
    return {"mensaje": "Actitud eliminada"}