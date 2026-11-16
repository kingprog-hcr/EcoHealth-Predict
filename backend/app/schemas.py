from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# SCHÉMAS UTILISATEURS 

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# SCHÉMAS TÉLÉMÉTRIE 

class SensorDataCreate(BaseModel):
    #user_id: int
    bpm: int
    spo2: float
    temperature: float
    contexte : str =  "rest" 

class SensorDataResponse(BaseModel):
    id: int
    user_id: int
    bpm: int
    spo2: float
    temperature: float
    contexte : str
    recorded_at: datetime

    class Config:
        from_attributes = True
        
class TelemetryPushResponse(BaseModel):
    measure : SensorDataResponse
    is_anomaly : bool
    anomalies : list[str]
    
class AlertResponse(BaseModel):
    id : int
    user_id : int
    sensor_data_id : int
    anomalies : str
    is_confirmed : Optional[bool] = False
    recorded_at : datetime
    
    class Config:
        from_attributes = True

# SCHÉMAS PRÉDICTIONS MACHINE LEARNING 

class PredictionCreate(BaseModel):
    user_id: int
    risk_score: float
    prediction_label: str

class PredictionResponse(BaseModel):
    id: int
    user_id: int
    risk_score: float
    prediction_label: str
    generated_at: datetime

    class Config:
        from_attributes = True