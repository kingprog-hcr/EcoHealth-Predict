FROM python:3.11-slim

# Repertoire de travail dans le conteneur
WORKDIR /app

# Copie et installation des dependances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le code du backend
COPY . .

# Exposer le port 8000
EXPOSE 8000

# Commande pour lancer FastAPI avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]