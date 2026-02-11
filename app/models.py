from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserBase(BaseModel):
    username: str
    password: str

class UserIn(UserBase):
    name: str

class UserDb(UserIn):
    id: int | None = None
    role: str | None = None

class UserOut(BaseModel):
    id: int
    name: str
    username: str
    role: str | None = None

class UserLoginIn(UserBase):
    pass

# MODELOS JSON
class UserCreateJson(BaseModel):
    email: str
    nombre: str
    contrasena: str

class UserEditJson(BaseModel):
    nombre: str
    
class UserChangePassword(BaseModel):
    old_password: str
    new_password: str

class UserEditProfile(BaseModel):
    name: str | None = None
    email: str | None = None

class UserUpdate(BaseModel):
    name: str
    username: str
    role: str

# MODELOS DE ALUMNOS
class StudentBase(BaseModel):
    name: str
    surname: str
    email: str
    age: int
    student_group: str

class StudentIn(StudentBase):
    pass

class StudentDb(StudentBase): # Hereda de StudentBase para tener todos los campos
    id: int | None = None

class StudentOut(StudentBase):
    id: int

class StudentLoginIn(StudentBase):
    pass

class StudentImportJson(BaseModel):
    name: str
    surname: str
    email: str
    age: int
    student_group: str

# MODELOS DE ACTITUDES
class CreateAttitude(BaseModel):
    student_email: str 
    type: str
    motive: str

class AttitudeUpdate(BaseModel):
    motive: str

class AttitudeOut(BaseModel):
    id: int
    description: str
    status: str
    teacher_name: str | None = None
    student_name: str | None = None
    type: str | None = None # WARNING o RECOGNITION