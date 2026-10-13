from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from app.database import Base

# 1. Table Utilisateurs
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "ecohealth"}

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 2. Table des données de télémétrie (Capteurs / Module C)
class SensorData(Base):
    __tablename__ = "sensor_data"
    __table_args__ = {"schema": "ecohealth"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("ecohealth.users.id", ondelete="CASCADE"), nullable=False)
    bpm = Column(Integer, nullable=False)
    spo2 = Column(Integer, nullable=False)
    temperature = Column(Numeric(4, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

# 3. Table des prédictions de Machine Learning
class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {"schema": "ecohealth"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("ecohealth.users.id", ondelete="CASCADE"), nullable=False)
    risk_score = Column(Numeric(5, 2), nullable=False)
    prediction_label = Column(String(50), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())