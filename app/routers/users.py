from urllib import response
from fastapi import APIRouter, status, HTTPException, Header
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

class UserBase(BaseModel):
    username: str
    password: str

class UserIn(UserBase):
    name: str

class UserDb(UserIn):
    id: int

class UserOut(BaseModel):
    id: int
    name: str
    username: str

class UserLoginIn(UserBase):
    pass

class TokenOut(BaseModel):
    token: str
    
users: list[UserDb] = []

@router.post("/signup/", status_code=status.HTTP_201_CREATED)
async def create_user(userIn: UserIn):
    usersFound = [u for u in users if u.username == userIn.username]
    if len(usersFound) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
        
    users.append(
        UserDb(
            id=len(users) + 1,
            name=userIn.name,
            username=userIn.username,
            password=userIn.password
        )
    )

@router.post( "/login/",response_model=TokenOut, status_code=status.HTTP_200_OK)
async def login(userLoginIn: UserLoginIn):
    usersFound = [u for u in users if u.username == userLoginIn.username]
    if not usersFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and/or password incorrect"
        )
    
    user:UserDb = usersFound[0]
    if user.password != userLoginIn.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and/or password incorrect"
        )
    return TokenOut(
        token=f"mytoken:{user.username}-{user.name}"
    )

@router.get("/", response_model=list[UserOut], status_code=status.HTTP_200_OK)
async def get_all_users(authorization: str = Header()):
    print(authorization)
    
    parts = authorization.split(":")
    if len(parts) != 2 or parts[0] != "mytoken":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden"
        )
    return [
        UserOut(id=userDb.id, name=userDb.name, username=userDb.username)
        for userDb in users
        ]