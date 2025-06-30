import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# === Load Data ===
df = pd.read_csv("crowdiness_dataset.csv")
X = df[["motion_rate", "avg_sound", "avg_co2"]]
y = df["crowdiness_index"]

# === Train-Test Split ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Train Model ===
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# === Evaluation ===
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"\n✅ Model Trained")
print(f"MSE: {mse:.4f}")
print(f"R² Score: {r2:.4f}")

# === Cross-Validation ===
cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
print(f"CV R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# === Save Model ===
joblib.dump(model, "owl_model.pkl")
print("📦 Model saved as owl_model.pkl")

# === Feature Importances ===
importances = model.feature_importances_
plt.figure(figsize=(5, 4))
plt.bar(X.columns, importances, color="teal")
plt.title("Feature Importances")
plt.tight_layout()
plt.savefig("feature_importance.png")
print("📊 Saved feature_importance.png")

# === Actual vs Predicted ===
plt.figure(figsize=(5, 5))
plt.scatter(y_test, y_pred, alpha=0.6)
plt.plot([0, 1], [0, 1], 'r--')
plt.xlabel("Actual")
plt.ylabel("Predicted")
plt.title("Actual vs Predicted Crowdiness")
plt.grid()
plt.tight_layout()
plt.savefig("prediction_vs_actual.png")
print("📈 Saved prediction_vs_actual.png")
