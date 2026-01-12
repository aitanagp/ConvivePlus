from app.database import users
from fastapi import APIRouter, status, HTTPException, Depends
from app.models import StudentIn, StudentDb, StudentOut, StudentLoginIn, StudentBase
from app.database import students, insert_student
from app.auth.auth import (
    create_access_token,
    Token,
    verify_password,
    oauth2_scheme,
    decode_token,
    TokenData,
)
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="v1/students", tags=["Students"])


@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(studentIn: StudentIn, token: str = Depends(oauth2_scheme)):
    decode_token(token)

    new_student = StudentDb(
        id=len(students) + 1,
        name=studentIn.name,
        surname=studentIn.surname,
        email=studentIn.email,
        age=studentIn.age,
    )

    insert_student(new_student)

    return new_student


@router.post("/login/", response_model=Token, status_code=status.HTTP_200_OK)
@router.get("/", response_model=list[StudentOut], status_code=status.HTTP_200_OK)
async def get_students(token: str = Depends(oauth2_scheme)):
    # 1. Decodificamos el token para saber quién es el usuario
    token_data: TokenData = decode_token(token)

    # 2.Verificamos si ese usuario existe realmente en nuestra lista de usuarios
    # Esto evita que alguien con un token viejo siga entrando
    user_exists = any(u.username == token_data.username for u in users)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed"
        )

    # 3. Si todo está bien, devolvemos la lista de alumnos
    return get_all_students()


@router.get("/", response_model=list[StudentOut], status_code=status.HTTP_200_OK)
async def get_all_students(token: str = Depends(oauth2_scheme)):
    data: TokenData = decode_token(token)

    if data.username not in [s.username for s in students]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return [
        StudentOut(
            id=studentDb.id,
            name=studentDb.name,
            surname=studentDb.surname,
            email=studentDb.email,
            age=studentDb.age,
        )
        for studentDb in students
    ]
