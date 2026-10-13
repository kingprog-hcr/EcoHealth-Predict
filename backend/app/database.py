import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
#pip install psycopg2-binary

from pathlib import Path
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


DB_USER = os.getenv("POSTGRES_USER", "admin") 
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret_password") #
DB_HOST = os.getenv("DB_HOST", "localhost")  # 'localhost' pour le dev local, 'db' sous Docker
DB_PORT = os.getenv("DB_PORT", "5432") 
DB_NAME = os.getenv("POSTGRES_DB", "ecohealth_db") 

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

# Gestion des sessions

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base pour les modèles ORM
Base = declarative_base()

# Dépendance FastAPI pour obtenir une session de BDD à chaque requête HTTP
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()