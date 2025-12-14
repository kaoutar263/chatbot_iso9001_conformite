from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from jose import JWTError, jwt
import sqlite3

from app.auth import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from app.database import get_db_connection, init_db

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/signup", response_model=Token)
async def signup(user: UserCreate):
    # Check if user exists
    conn = get_db_connection()
    cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = get_password_hash(user.password)
    conn.execute("INSERT INTO users (email, hashed_password, created_at) VALUES (?, ?, datetime('now'))", 
                 (user.email, hashed))
    conn.commit()
    conn.close()
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.execute("SELECT hashed_password FROM users WHERE email = ?", (form_data.username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(form_data.password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    conn = get_db_connection()
    cursor = conn.execute("SELECT id, email FROM users WHERE email = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
    return {"id": user[0], "email": user[1]}
