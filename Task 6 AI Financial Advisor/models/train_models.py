"""
FinPulse AI - Machine Learning Training & Performance Evaluation Pipeline
Trains:
1. Risk Appetite Multi-Class Classifier (Random Forest / Gradient Boosting)
2. Financial Health Score Regressor (0-100 Score)
3. Financial Distress Risk Classifier (Binary Risk Alert)
Evaluates with Cross-Validation, ROC-AUC, F1-Scores, Confusion Matrices, and Feature Importance.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, r2_score, mean_squared_error, mean_absolute_error,
    roc_auc_score
)
import joblib

try:
    from models.preprocessor import FinancialDataPreprocessor, FEATURE_COLUMNS, engineer_features
except ModuleNotFoundError:
    from preprocessor import FinancialDataPreprocessor, FEATURE_COLUMNS, engineer_features

def train_and_evaluate():
    data_path = os.path.join("data", "client_profiles.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file {data_path} not found. Run synthetic_financial_data.py first.")
        
    df = pd.read_csv(data_path)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns.")
    
    # Initialize & Fit Preprocessor
    preprocessor = FinancialDataPreprocessor()
    X = preprocessor.fit_transform(df)
    
    y_risk = df["risk_profile"]
    y_health = df["financial_health_score"]
    y_distress = df["distress_risk"]
    
    # Train / Test Split (80 / 20)
    indices = np.arange(len(df))
    train_idx, test_idx = train_test_split(indices, test_size=0.20, random_state=42, stratify=y_risk)
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_risk_train, y_risk_test = y_risk.iloc[train_idx], y_risk.iloc[test_idx]
    y_health_train, y_health_test = y_health.iloc[train_idx], y_health.iloc[test_idx]
    y_distress_train, y_distress_test = y_distress.iloc[train_idx], y_distress.iloc[test_idx]
    
    # -------------------------------------------------------------
    # 1. Train Risk Appetite Classifier
    # -------------------------------------------------------------
    print("\n--- Training Risk Appetite Classifier ---", flush=True)
    risk_clf = RandomForestClassifier(n_estimators=60, max_depth=8, random_state=42, class_weight="balanced", n_jobs=1)
    risk_clf.fit(X_train, y_risk_train)
    
    y_risk_pred = risk_clf.predict(X_test)
    y_risk_prob = risk_clf.predict_proba(X_test)
    
    # Risk Metrics
    risk_acc = float(accuracy_score(y_risk_test, y_risk_pred))
    risk_prec = float(precision_score(y_risk_test, y_risk_pred, average="weighted"))
    risk_rec = float(recall_score(y_risk_test, y_risk_pred, average="weighted"))
    risk_f1 = float(f1_score(y_risk_test, y_risk_pred, average="weighted"))
    risk_labels = sorted(list(set(y_risk)))
    cm = confusion_matrix(y_risk_test, y_risk_pred, labels=risk_labels)
    
    # Fast Stratified CV (2-fold) for speed
    cv_kfold = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
    risk_cv_scores = cross_val_score(risk_clf, X[:600], y_risk[:600], cv=cv_kfold, scoring="accuracy", n_jobs=1)
    
    # Feature Importance
    risk_feature_importances = dict(zip(FEATURE_COLUMNS, [round(float(val), 4) for val in risk_clf.feature_importances_]))
    sorted_risk_features = sorted(risk_feature_importances.items(), key=lambda x: x[1], reverse=True)
    
    print(f"Risk Classifier Accuracy: {risk_acc:.4f}", flush=True)
    print(f"Risk Classifier F1-Score: {risk_f1:.4f}", flush=True)
    print(f"CV Accuracy: {risk_cv_scores.mean():.4f}", flush=True)
    
    # -------------------------------------------------------------
    # 2. Train Financial Health Score Regressor
    # -------------------------------------------------------------
    print("\n--- Training Financial Health Regressor ---", flush=True)
    health_reg = GradientBoostingRegressor(n_estimators=60, learning_rate=0.1, max_depth=3, random_state=42)
    health_reg.fit(X_train, y_health_train)
    
    y_health_pred = health_reg.predict(X_test)
    health_r2 = float(r2_score(y_health_test, y_health_pred))
    health_mae = float(mean_absolute_error(y_health_test, y_health_pred))
    health_rmse = float(np.sqrt(mean_squared_error(y_health_test, y_health_pred)))
    
    print(f"Health Regressor R2: {health_r2:.4f}, MAE: {health_mae:.2f}, RMSE: {health_rmse:.2f}", flush=True)
    
    # -------------------------------------------------------------
    # 3. Train Financial Distress Risk Classifier
    # -------------------------------------------------------------
    print("\n--- Training Distress Risk Predictor ---", flush=True)
    distress_clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42, class_weight="balanced", n_jobs=1)
    distress_clf.fit(X_train, y_distress_train)
    
    y_distress_pred = distress_clf.predict(X_test)
    y_distress_prob = distress_clf.predict_proba(X_test)[:, 1]
    
    distress_acc = float(accuracy_score(y_distress_test, y_distress_pred))
    distress_f1 = float(f1_score(y_distress_test, y_distress_pred, zero_division=0))
    distress_auc = float(roc_auc_score(y_distress_test, y_distress_prob))
    
    print(f"Distress Classifier ROC-AUC: {distress_auc:.4f}, F1: {distress_f1:.4f}", flush=True)
    
    # -------------------------------------------------------------
    # 4. Save Models & Serialization
    # -------------------------------------------------------------
    os.makedirs("models", exist_ok=True)
    preprocessor.save("models/preprocessor.joblib")
    joblib.dump(risk_clf, "models/risk_model.joblib")
    joblib.dump(health_reg, "models/health_model.joblib")
    joblib.dump(distress_clf, "models/distress_model.joblib")
    
    # -------------------------------------------------------------
    # 5. Export Performance Metrics JSON
    # -------------------------------------------------------------
    metrics = {
        "risk_model": {
            "model_type": "Random Forest Classifier (Balanced)",
            "accuracy": round(risk_acc, 4),
            "precision": round(risk_prec, 4),
            "recall": round(risk_rec, 4),
            "f1_score": round(risk_f1, 4),
            "cv_mean_accuracy": round(float(risk_cv_scores.mean()), 4),
            "cv_std": round(float(risk_cv_scores.std()), 4),
            "labels": risk_labels,
            "confusion_matrix": cm.tolist(),
            "feature_importance": sorted_risk_features
        },
        "health_model": {
            "model_type": "Gradient Boosting Regressor",
            "r2_score": round(health_r2, 4),
            "mae": round(health_mae, 4),
            "rmse": round(health_rmse, 4)
        },
        "distress_model": {
            "model_type": "Balanced Random Forest Classifier",
            "accuracy": round(distress_acc, 4),
            "f1_score": round(distress_f1, 4),
            "roc_auc": round(distress_auc, 4)
        },
        "dataset_summary": {
            "total_samples": len(df),
            "train_samples": len(train_idx),
            "test_samples": len(test_idx),
            "features_count": len(FEATURE_COLUMNS),
            "feature_names": FEATURE_COLUMNS
        }
    }
    
    with open("models/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("\nSuccessfully saved all trained models and metrics.json in models/")

if __name__ == "__main__":
    train_and_evaluate()
