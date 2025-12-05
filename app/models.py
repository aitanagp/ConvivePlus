from pydantic import BaseModel

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
