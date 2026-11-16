CREATE SCHEMA IF NOT EXISTS ecohealth;

-- Table des utilisateurs

CREATE TABLE ecohealth.users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des mesures de télémétrie alimentée par le programme C
CREATE TABLE ecohealth.sensor_data (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES ecohealth.users(id) ON DELETE CASCADE,
    bpm INT NOT NULL,
    spo2 INT NOT NULL,
    temperature NUMERIC(4, 2) NOT NULL,
    contexte VARCHAR(50) NOT NULL DEFAULT 'rest',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des prédictions du modèle de Machine Learning
CREATE TABLE ecohealth.predictions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES ecohealth.users(id) ON DELETE CASCADE,
    risk_score NUMERIC(5, 2) NOT NULL,
    prediction_label VARCHAR(50) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des alertes (Derive Biomedicale)

CREATE TABLE ecohealth.alerts (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES ecohealth.users(id) ON DELETE CASCADE,
    sensor_data_id INT REFERENCES ecohealth.sensor_data(id) ON DELETE CASCADE,
    anomalies VARCHAR(255) NOT NULL,
    is_confirmed BOOLEAN NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--Création automatique d'un utilisateur de test (Email: anne@chrys.com | Mot de passe: camille) 
INSERT INTO ecohealth.users (full_name, email, hashed_password)
VALUES ( 
    'Anne Chrys',
    'anne@chrys.com',
    '$2b$12$6dCK51K/xgBeTarjCE0NC.5.6bbuOakGqrPCgP8UD8fdXhD2zNOQa'
     )
ON CONFLICT (email) DO NOTHING;