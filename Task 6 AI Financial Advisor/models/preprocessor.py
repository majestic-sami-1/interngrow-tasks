"""
FinPulse AI - Preprocessing & Feature Engineering Pipeline
Handles input data cleaning, feature derivation, ratio computation,
outlier clipping, and feature scaling for inference and model training.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import os

FEATURE_COLUMNS = [
    "age",
    "annual_income",
    "monthly_expenses",
    "dependents",
    "credit_score",
    "total_debt",
    "monthly_debt_payment",
    "current_savings",
    "current_investments",
    "investment_horizon",
    "dti_ratio",
    "savings_rate",
    "emergency_months",
    "net_worth",
    "wealth_to_income",
    "debt_to_assets"
]

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive financial domain features and ratio metrics."""
    data = df.copy()
    
    # Ensure numerical datatypes
    for col in ["age", "annual_income", "monthly_expenses", "dependents", "credit_score",
                "total_debt", "monthly_debt_payment", "current_savings", "current_investments", "investment_horizon"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)
            
    # Calculate key ratios if not already present or refresh them
    monthly_income = np.maximum(data["annual_income"] / 12.0, 1.0)
    
    data["dti_ratio"] = np.clip((data["monthly_debt_payment"] * 12.0) / np.maximum(data["annual_income"], 1.0), 0.0, 1.5)
    
    disposable_monthly = monthly_income - data["monthly_expenses"] - data["monthly_debt_payment"]
    data["savings_rate"] = np.clip(disposable_monthly / monthly_income, -0.5, 0.9)
    
    data["emergency_months"] = np.clip(data["current_savings"] / np.maximum(data["monthly_expenses"], 1.0), 0.0, 60.0)
    
    data["net_worth"] = data["current_savings"] + data["current_investments"] - data["total_debt"]
    
    total_assets = data["current_savings"] + data["current_investments"]
    data["wealth_to_income"] = np.clip(total_assets / np.maximum(data["annual_income"], 1.0), 0.0, 50.0)
    data["debt_to_assets"] = np.clip(data["total_debt"] / np.maximum(total_assets, 100.0), 0.0, 10.0)
    
    return data

class FinancialDataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = FEATURE_COLUMNS
        self.is_fitted = False
        
    def fit(self, df: pd.DataFrame):
        engineered = engineer_features(df)
        X = engineered[self.feature_columns]
        self.scaler.fit(X)
        self.is_fitted = True
        return self
        
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("FinancialDataPreprocessor has not been fitted yet.")
        engineered = engineer_features(df)
        X = engineered[self.feature_columns]
        return self.scaler.transform(X)
        
    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)
        
    def preprocess_single(self, client_data: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, float]]:
        """Preprocesses a single user profile dictionary into scaled features + computed ratios."""
        df_single = pd.DataFrame([client_data])
        engineered = engineer_features(df_single)
        scaled = self.transform(engineered)
        
        computed_ratios = {
            "dti_ratio": float(engineered["dti_ratio"].iloc[0]),
            "savings_rate": float(engineered["savings_rate"].iloc[0]),
            "emergency_months": float(engineered["emergency_months"].iloc[0]),
            "net_worth": float(engineered["net_worth"].iloc[0]),
            "wealth_to_income": float(engineered["wealth_to_income"].iloc[0]),
            "debt_to_assets": float(engineered["debt_to_assets"].iloc[0])
        }
        return scaled, computed_ratios

    def save(self, filepath: str = "models/preprocessor.joblib"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str = "models/preprocessor.joblib") -> "FinancialDataPreprocessor":
        import sys
        models_dir = os.path.dirname(os.path.abspath(__file__))
        if models_dir not in sys.path:
            sys.path.insert(0, models_dir)
        import models.preprocessor as mp
        sys.modules["preprocessor"] = mp
        return joblib.load(filepath)
