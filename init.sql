CREATE SCHEMA IF NOT EXISTS ecohealth;

-- Table des utilisateurs

CREATE TABLE ecohealth.users (
    id SERIAL PRIMARY KEY,
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