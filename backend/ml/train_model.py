# %%
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# %%
df = pd.read_csv("data/vital_signs_dataset.csv") 
df.head()

# %%
# features
features = ['bpm', 'spo2', 'temperature']
X = df[features]
X.head

# %%
y = df['risk_level']

# %%
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, random_state=42)

# %%
model = RandomForestClassifier(random_state=42, n_estimators=100)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
acc = accuracy_score(y_test, predictions) 
print(f"Précision globale : {acc * 100:.2f}%")

# %%
model.score(X_test, y_test)

print(classification_report(y_test, predictions))

# %%
from sklearn.metrics import ConfusionMatrixDisplay
# Affichage de la matrice de confusion 
plt.figure(figsize=(7, 5)) 
ConfusionMatrixDisplay.from_predictions( y_test, predictions, display_labels=['Normal (0)', 'Modéré (1)', 'Alerte (2)'], cmap=plt.cm.Blues )
plt.title("Matrice de Confusion - Risque de Santé") 
plt.grid(False)
plt.show()

# %%
# Extraction de l'importance des variables
importances = model.feature_importances_

plt.figure(figsize=(7, 4))
plt.bar(features, importances, color=['#3498db', '#e74c3c', '#2ecc71'])
plt.title("Importance des Constantes Vitales dans la Prédiction")
plt.xlabel("Variables Biométriques")
plt.ylabel("Score d'Importance")
plt.ylim(0, 1)

# Affichage des valeurs au-dessus des barres
for i, v in enumerate(importances):
    plt.text(i, v + 0.02, f"{v*100:.1f}%", ha='center', fontweight='bold')

plt.show()


# %%

import joblib

# Sauvegarde du modèle entraîné dans le sous-dossier ml/
joblib.dump(model, 'first_model.joblib')
print("✅ Modèle sauvegardé avec succès sous 'ml/model.joblib' !")

#ttest du model
# Chargement  modèle depuis le fichier .joblib
loaded_model = joblib.load('first_model.joblib')

# Tester une prédiction à chaud : BPM = 120, SpO2 = 90%, Temp = 38.8°C (Cas Alerte / 2)
test_patient = [[120, 90.0, 38.8]]
prediction_test = loaded_model.predict(test_patient)
proba_test = loaded_model.predict_proba(test_patient)

print(f"Classe prédite : {prediction_test[0]}") 
print(f"Probabilités par classe [Normal, Modéré, Alerte] : {proba_test[0]}")



