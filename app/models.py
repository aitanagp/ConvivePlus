from pydantic import BaseModel

# --- MODELOS DE USUARIO ---

class UserBase(BaseModel):
    username: str
    password: str

class UserIn(UserBase):
    name: str

class UserDb(UserIn):
    id: int | None = None

class UserOut(BaseModel):
    id: int
    name: str
    username: str

class UserLoginIn(UserBase):
    pass

# --- MODELOS DE ALUMNOS ---

class StudentBase(BaseModel):
    name: str
    surname: str
    email: str
    age: int

class StudentIn(StudentBase):
    name: str

class StudentDb(StudentIn):
    id: int | None = None

class StudentOut(StudentBase):
    id: int

class StudentLoginIn(StudentBase):
    pass
