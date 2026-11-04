
import pandas as pd

# Constantes et  Dictionnaire des anomalies
BIO_VALS = ['bpm', 'spo2', 'temperature']

ANOMALIES_MAP = {
    "TACHYCARDIA_REST": "Anomalie : Fréquence cardiaque anormalement élevée au repos",
    "HYPOXIA": "Anomalie : Saturation en oxygène critique (&lt; 94%)",
    "FEVER": "Anomalie : Température corporelle élevée / Fièvre (≥ 38°C)"
}

def calculate_user_baseline(df: pd.DataFrame, user_id: str) -> pd.DataFrame:
    """Calcule l'écart-type et la moyenne du patient au repos.

    Args:
        df (pd.DataFrame): DataFrame contenant les données biométriques.
        user_id (str): Identifiant unique du patient (colonne 'patient_id').

    Returns:
        pd.DataFrame: DataFrame indexé par constante biométrique ('bpm', 'spo2', 'temperature')
                      avec les colonnes 'moyenne' et 'ecart_type'.
    """
    # Filtrage des données du patient au repos
    df_user = df[(df['patient_id'] == user_id) & (df['context'] == 'rest')]

    means = []
    ecart_types = []

    # Calcul des moyennes
    for val in BIO_VALS:
        means.append(df_user[val].mean())

    # Calcul et sécurisation des écarts-types
    for val in BIO_VALS:
        ecart_type = df_user[val].std()
        # si std est NaN (1 seule mesure) ou égal à 0, on le fixe à 1.0 pour éviter div/0
        if pd.isna(ecart_type) or ecart_type == 0:
            ecart_type = 1.0
        ecart_types.append(ecart_type)

    baseline_df = pd.DataFrame({
        'moyenne': means,
        'ecart_type': ecart_types
    }, index=BIO_VALS)

    return baseline_df

def evaluate_telemetry(baseline: pd.DataFrame, bpm: float, spo2: float, temperature: float) -> list:
    """Évalue une mesure instantanée en temps réel et retourne la liste des anomalies détectées.

    Args:
        baseline (pd.DataFrame): DataFrame de référence calculé par calculate_user_baseline.
        bpm (float): Fréquence cardiaque mesurée (en BPM).
        spo2 (float): Saturation en oxygène mesurée (en %).
        temperature (float): Température corporelle mesurée (en °C).

    Returns:
        list: Liste des codes d'anomalies détectées (ex: ["HYPOXIA", "FEVER"]).
              Renvoie une liste vide [] si la mesure est normale.
    """
    anomalies = []

    # 1. Extraction propre des statistiques de repos pour le BPM
    mean_bpm = baseline.loc['bpm', 'moyenne']
    std_bpm = baseline.loc['bpm', 'ecart_type']

    # Calcul du Z-Score (déviation par rapport à la moyenne de repos)
    z_bpm = (bpm - mean_bpm) / std_bpm

    # 3. Détection des anomalies (accumulation sans return prématuré)
    if z_bpm > 3.0:
        anomalies.append("TACHYCARDIA_REST")

    if spo2 < 94.0:
        anomalies.append("HYPOXIA")

    if temperature >= 38.0:
        anomalies.append("FEVER")

    return anomalies

