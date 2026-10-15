from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, SensorData
from app.schemas import UserCreate, UserResponse, SensorDataCreate, SensorDataResponse
from app.auth import get_password_hash, verify_password, create_access_token,create_refresh_token, decode_token, get_current_user

from dotenv import load_dotenv
import os

load_dotenv()

#ajouter des favicon
app = FastAPI(
    title="EcoHealth Predict API",
    version="1.0.0",
    description="API de gestion de télémétrie et de prédictions santé/énergie"
)

raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [origin.strip() for origin in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Bienvenue sur l'API EcoHealth Predict !"}

@app.get("/item/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.get("/users/{user_id}")
def read_user_profile(user_id : int, q : str | None = None):
    return {
        "user_id" : user_id,
        "Nom" : "",
        "email" : ""
    }

@app.post("/api/v1/auth/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)) -> UserResponse | None:
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
        
    full_name = user_data.full_name
    email = user_data.email
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        full_name = full_name,
        hashed_password = hashed_password,
        email = email
    )
    
    db.add(user)
    db.commit()
    db.refresh(user) 
    
    return user
    

@app.post("/api/v1/auth/login")
def connect_user( form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    
    detail = "Email ou mot de passe incorrect"
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail=detail)
        
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
    return {"access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"}
    

@app.get("/api/v1/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/api/v1/auth/refresh")
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    # 1. Décodage et vérification de la signature / expiration
    payload = decode_token(refresh_token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")
    
    # Vérification du type de jeton
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Type de jeton invalide")
    
    user_id = payload.get("sub")
    
    # Verification de l'utilisateur en BDD
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    # Génération d'un tout nouvel access_token
    new_access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


# Gestion des routes de la telemetrie :

@app.post("/api/v1/telemetry/push", response_model=SensorDataResponse)
def push_telemetry(
    data: SensorDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_measure = SensorData(
        user_id=current_user.id,
        bpm=data.bpm,
        spo2=data.spo2,
        temperature=data.temperature
    )
    db.add(new_measure)
    db.commit()
    db.refresh(new_measure)
    return new_measure

@app.get("/api/v1/telemetry/history", response_model=list[SensorDataResponse])
def get_telemetry_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(SensorData)
        .filter(SensorData.user_id == current_user.id)
        .order_by(SensorData.recorded_at.desc())
        .limit(limit)
        .all()
    )