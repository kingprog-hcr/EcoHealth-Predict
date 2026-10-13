import os
import jwt
import bcrypt
from dotenv import load_dotenv
from datetime import timezone, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "4r948frnv03f390wnd043f3f398f3necomadfmcrfr")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )
    
    
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str :
    
    if expires_delta == None :
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    exp_date = datetime.now(timezone.utc) +  expires_delta
    data_to_encode = data.copy()
    data_to_encode.update({"exp": exp_date, "type" : "access"})
    
    return jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    
def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None     
   


# Definit l'URL vers laquelle le client doit envoyer ses identifiants
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les jetons d'accès",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    #  Décodage du token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    #  Récupération du user_id
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    #  Vrification de l'existence de l'utilisateur en BDD
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return user