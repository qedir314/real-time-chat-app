import os
from datetime import datetime, timedelta, UTC
from typing import Optional

from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from config.database import users_collection

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin", auto_error=False)


def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False
    # bcrypt.checkpw expects bytes
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str):
    # Truncate password to 72 bytes if it's longer, as bcrypt has this limit
    encoded_password = password.encode('utf-8')
    if len(encoded_password) > 72:
        password = encoded_password[:72].decode('utf-8', errors='ignore')
        encoded_password = password.encode('utf-8')
        
    hashed = bcrypt.hashpw(encoded_password, bcrypt.gensalt())
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_token(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    if token:
        return token
    
    # Check cookie if header is missing
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:]
        return cookie_token
    
    return None


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    user = users_collection.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"])
        # Check if user is admin
        admin_username = os.getenv("ADMIN_USERNAME")
        user["is_admin"] = admin_username and user["username"] == admin_username
    return user


def get_current_active_user(token: str = Depends(get_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
