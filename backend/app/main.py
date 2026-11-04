from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SensorData, Alert
from app.schemas import UserCreate, UserResponse, SensorDataCreate, SensorDataResponse, AlertResponse, TelemetryPushResponse
from app.auth import get_password_hash, verify_password, create_access_token,create_refresh_token, decode_token, get_current_user

import pandas as pd
from ml.engine import calculate_user_baseline, evaluate_telemetry


from dotenv import load_dotenv
import os

load_dotenv()

# 1Création du limiteur basé sur l'adresse IP du client
limiter = Limiter(key_func=get_remote_address)

# note : ajouter des favicon
app = FastAPI(
    title="EcoHealth Predict API",
    version="1.0.0",
    description="API de gestion de télémétrie et de prédictions santé/énergie"
)

# Liaison du limiteur à l'état de l'application FastAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
@limiter.limit("5/minute")
def connect_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict:

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
    # Décodage et vérification de la signature / expiration
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

@app.post("/api/v1/telemetry/push", response_model=TelemetryPushResponse)
@limiter.limit("60/minute")
def push_telemetry(
    request: Request,
    data: SensorDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enregistre une nouvelle mesure de télémétrie, évalue la dérive biomédicale 
    par rapport à la baseline du patient et enregistre une alerte si nécessaire.
    """
    # Sauvegarde systématique de la nouvelle mesure en base de données
    new_measure = SensorData(
        user_id=current_user.id,
        bpm=data.bpm,
        spo2=data.spo2,
        temperature=data.temperature,
        contexte=data.contexte
    )
    db.add(new_measure)
    db.commit()
    db.refresh(new_measure)  #

    # Récupération de l'historique complet des mesures du patient
    history = db.query(SensorData).filter(SensorData.user_id == current_user.id).all()

    #  Gestion du Cold Start (historique insuffisant pour calculer un Z-Score fiable)
    if len(history) < 5:
        return TelemetryPushResponse(
            measure=new_measure,
            is_anomaly=False,
            anomalies=[]
        )

    # Conversion de l'historique SQLAlchemy en DataFrame Pandas
    df = pd.DataFrame([
        {
            "patient_id": str(m.user_id),
            "bpm": m.bpm,
            "spo2": m.spo2,
            "temperature": float(m.temperature),
            "context": m.contexte
        }
        for m in history
    ])

    # Calcul de la baseline au repos et évaluation biomédicale en temps réel
    baseline = calculate_user_baseline(df, str(current_user.id))
    anomalies = evaluate_telemetry(baseline, data.bpm, data.spo2, data.temperature)

    # Si des anomalies sont détectées, création et stockage de l'alerte
    if anomalies:
        anomalies_str = ",".join(anomalies)  # Conversion en str
        alert = Alert(
            user_id=current_user.id,
            sensor_data_id=new_measure.id,  # Clé étrangère vers la mesure enregistrée
            anomalies=anomalies_str,
            is_confirmed=False
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

    # Retour au client (Boîtier C / Frontend)
    return TelemetryPushResponse(
        measure=new_measure,
        is_anomaly=len(anomalies) > 0,
        anomalies=anomalies
    )

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
