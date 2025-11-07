from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

class UserDb(BaseModel):
    id: int
    name: str
    username: str
    password: str
    
class UserIn(BaseModel):
    username: str
    password: str
    name: str
    
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