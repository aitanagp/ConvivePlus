from pydantic import BaseModel
from datetime import date, time
from typing import List, Dict

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
    department: str | None = None

class UserOut(BaseModel):
    id: int
    name: str
    username: str
    role: str | None = None
    department: str | None = None

class UserLoginIn(UserBase):
    pass

# MODELOS JSON
class UserCreate(BaseModel):
    username: str
    name: str
    password: str
    role: str = "TEACHER"
    department: str | None = None

class UserCreateJson(BaseModel):
    email: str
    nombre: str
    contrasena: str
    departamento: str | None = None

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
    department: str | None = None

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
    is_probi: bool = False

class StudentLoginIn(StudentBase):
    pass

class StudentImportJson(BaseModel):
    name: str
    surname: str
    email: str
    age: int
    student_group: str

class StudentUpdate(BaseModel): # Este es para cuando editamos un alumno
    name: str | None = None
    surname: str | None = None
    email: str | None = None
    age: int | None = None
    student_group: str | None = None

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

# MODELOS DE AULA DE CONVIVENCIA
class ClassroomAssignmentIn(BaseModel):
    student_id: int
    start_date: date
    end_date: date
    start_time: time
    end_time: time

class ClassroomTaskIn(BaseModel):
    assignment_id: int
    description: str

class AttendanceUpdate(BaseModel):
    assignment_id: int
    attendance_date: date
    status: str # PRESENTE o AUSENTE

# MODELOS DE EXPEDIENTES DISCIPLINARIOS
class DisciplinaryRecordOpen(BaseModel):
    student_id: int
    attitude_ids: List[int]
    observations: str | None = ""

class DisciplinaryRecordStatusUpdate(BaseModel):
    status: str # Abierto, En trámite, Cerrado, Sancionado
    observations: str | None = None

class DisciplinaryRecordOut(BaseModel):
    id: int
    student_id: int
    start_date: date
    status: str
    observations: str

# MODELOS DE CURSO ACADÉMICO
class AcademicYearIn(BaseModel):
    start_year: int
    end_year: int

class AcademicYearOut(AcademicYearIn):
    id: int
    is_active: bool

# --- MODELOS DE ESTADÍSTICAS ---
class StatsSummary(BaseModel):
    warnings: int
    recognitions: int
    total: int

class GroupStats(BaseModel):
    student_group: str
    warnings: int
    recognitions: int

class TopStudentStats(BaseModel):
    student_id: int
    name: str
    surname: str
    student_group: str
    count: int