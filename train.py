"""
WeatherGPT ML Training Pipeline (Supervised Learning)
====================================================
Trains 3 Random Forest models offline using historical weather data:
1. Regression: Next-Day Temperature (°C) -> RandomForestRegressor
2. Binary Classification: Next-Day Rain (0 or 1) -> RandomForestClassifier
3. Multi-Class Classification: Weather Condition (Sunny/Cloudy/Rainy/Foggy) -> RandomForestClassifier

Run:
    python train.py
"""

import os
import json
import joblib
from datetime import datetime
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

from src.features import prepare_training_data, FEATURE_COLUMNS, CITY_MAP


def train_and_evaluate(
    dataset_path: str = "data/weather_historical.csv",
    model_output_path: str = "models/weather_model.pkl"
):
    """
    End-to-end training and evaluation workflow:
    1. Loads dataset and extracts engineered features
    2. Splits into 80% train and 20% test sets
    3. Trains temperature regressor
    4. Trains rain classifier
    5. Trains condition classifier
    6. Saves metrics to models/metrics.json and model bundle to models/weather_model.pkl
    """
    print("=" * 70)
    print("   🌤️ WeatherGPT Supervised ML Training Pipeline (scikit-learn)")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Step 1: Load and Preprocess Data
    # -------------------------------------------------------------------------
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset '{dataset_path}' not found! Run 'python src/dataset_generator.py' first."
        )

    print(f"\n[Step 1/5] Loading historical dataset from: {dataset_path}")
    X, y_temp, y_rain, y_cond = prepare_training_data(dataset_path)
    print(f"  ✓ Total historical samples: {len(X)}")
    print(f"  ✓ Features count: {X.shape[1]}")
    print(f"  ✓ Feature list: {list(X.columns)}")

    # -------------------------------------------------------------------------
    # Step 2: Split Data into Training (80%) and Testing (20%) Sets
    # -------------------------------------------------------------------------
    print("\n[Step 2/5] Splitting dataset (80% Training, 20% Unseen Testing)...")
    (
        X_train, X_test,
        y_temp_train, y_temp_test,
        y_rain_train, y_rain_test,
        y_cond_train, y_cond_test
    ) = train_test_split(
        X, y_temp, y_rain, y_cond,
        test_size=0.20,
        random_state=42,
        stratify=y_rain  # Keeps balanced proportion of rainy vs dry days in both splits
    )
    print(f"  ✓ Training records: {len(X_train)}")
    print(f"  ✓ Test records:     {len(X_test)}")

    # -------------------------------------------------------------------------
    # Step 3: Train Model 1 — Temperature Regressor
    # -------------------------------------------------------------------------
    print("\n[Step 3/5] Training Model 1: Temperature Regressor (RandomForestRegressor)...")
    temp_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    temp_model.fit(X_train, y_temp_train)
    y_temp_pred = temp_model.predict(X_test)

    temp_mae = float(mean_absolute_error(y_temp_test, y_temp_pred))
    temp_rmse = float(np.sqrt(mean_squared_error(y_temp_test, y_temp_pred)))
    temp_r2 = float(r2_score(y_temp_test, y_temp_pred))

    print(f"  --> Temperature Regression Evaluation:")
    print(f"      • Mean Absolute Error (MAE):     {temp_mae:.2f} °C")
    print(f"      • Root Mean Squared Error (RMSE): {temp_rmse:.2f} °C")
    print(f"      • R² Score (Variance Explained):  {temp_r2:.4f}")

    # -------------------------------------------------------------------------
    # Step 4: Train Model 2 — Rain Classifier (Binary: 0 or 1)
    # -------------------------------------------------------------------------
    print("\n[Step 4/5] Training Model 2: Rain Classifier (RandomForestClassifier)...")
    rain_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    rain_model.fit(X_train, y_rain_train)
    y_rain_pred = rain_model.predict(X_test)
    y_rain_proba = rain_model.predict_proba(X_test)[:, 1]

    rain_acc = float(accuracy_score(y_rain_test, y_rain_pred))
    rain_prec = float(precision_score(y_rain_test, y_rain_pred, zero_division=0))
    rain_rec = float(recall_score(y_rain_test, y_rain_pred, zero_division=0))
    rain_f1 = float(f1_score(y_rain_test, y_rain_pred, zero_division=0))
    rain_auc = float(roc_auc_score(y_rain_test, y_rain_proba))
    cm = confusion_matrix(y_rain_test, y_rain_pred).tolist()

    print(f"  --> Rain Classification Evaluation:")
    print(f"      • Accuracy:          {rain_acc * 100:.2f}%")
    print(f"      • Precision:         {rain_prec:.4f}")
    print(f"      • Recall:            {rain_rec:.4f}")
    print(f"      • F1-Score:          {rain_f1:.4f}")
    print(f"      • ROC-AUC Score:     {rain_auc:.4f}")
    print(f"      • Confusion Matrix:  TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")

    # -------------------------------------------------------------------------
    # Step 5: Train Model 3 — Weather Condition Classifier (Multi-class)
    # -------------------------------------------------------------------------
    print("\n[Step 5/5] Training Model 3: Weather Condition Classifier...")
    cond_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    cond_model.fit(X_train, y_cond_train)
    y_cond_pred = cond_model.predict(X_test)
    cond_acc = float(accuracy_score(y_cond_test, y_cond_pred))
    cond_f1 = float(f1_score(y_cond_test, y_cond_pred, average="macro", zero_division=0))

    print(f"  --> Condition Classification Evaluation:")
    print(f"      • Multi-class Accuracy:  {cond_acc * 100:.2f}%")
    print(f"      • Macro F1-Score:        {cond_f1:.4f}")

    # Calculate Feature Importances
    importances_temp = {col: round(float(imp), 4) for col, imp in zip(FEATURE_COLUMNS, temp_model.feature_importances_)}
    importances_rain = {col: round(float(imp), 4) for col, imp in zip(FEATURE_COLUMNS, rain_model.feature_importances_)}

    # Save summary metrics to dictionary
    metrics_summary = {
        "train_timestamp": datetime.now().isoformat(),
        "total_samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "temperature_regression": {
            "mae": temp_mae,
            "rmse": temp_rmse,
            "r2_score": temp_r2,
            "unit": "°C"
        },
        "rain_classification": {
            "accuracy": rain_acc,
            "precision": rain_prec,
            "recall": rain_rec,
            "f1_score": rain_f1,
            "roc_auc": rain_auc,
            "confusion_matrix": cm
        },
        "condition_classification": {
            "accuracy": cond_acc,
            "macro_f1": cond_f1
        },
        "feature_importances": {
            "temperature": importances_temp,
            "rain": importances_rain
        }
    }

    # Save metrics JSON file
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    metrics_path = os.path.join(os.path.dirname(model_output_path), "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"\n  ✓ Metrics report saved to: {metrics_path}")

    # Save model bundle (.pkl) using joblib
    model_bundle = {
        "temp_model": temp_model,
        "rain_model": rain_model,
        "cond_model": cond_model,
        "feature_columns": FEATURE_COLUMNS,
        "city_map": CITY_MAP,
        "condition_classes": list(cond_model.classes_),
        "metrics": metrics_summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    joblib.dump(model_bundle, model_output_path)
    print(f"  ✓ Serialized model bundle saved to: {model_output_path}")

    print("\n" + "=" * 70)
    print("   ✅ Training Complete! Ready for Offline WeatherGPT Predictions.")
    print("=" * 70)

    return model_bundle, metrics_summary


if __name__ == "__main__":
    train_and_evaluate()
