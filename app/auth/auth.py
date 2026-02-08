import bcrypt

from datetime import datetime, timedelta
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

from app.models import UserBase

SECRET_KEY = "1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 7 * 24 * 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login/")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def get_hash_password(plain_pw: str) -> str:
    pw_bytes = plain_pw.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password=pw_bytes, salt=salt)
    return hashed_pw.decode('utf-8')

def verify_password(plain_pw, hashed_pw) -> bool:
    plain_pw_bytes = plain_pw.encode("utf-8")
    hashed_pw_bytes = hashed_pw.encode("utf-8")
    return bcrypt.checkpw(password=plain_pw_bytes, hashed_password=hashed_pw_bytes)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt 

def decode_token(token: str) -> TokenData:
    try:
        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(username=payload.get("sub"))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


