"""
Unit tests for Machine Learning Preprocessing and Model Inference.
"""

import unittest
import os
import sys
import numpy as np
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.preprocessor import FinancialDataPreprocessor

class TestMLInference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preprocessor = FinancialDataPreprocessor.load("models/preprocessor.joblib")
        cls.risk_model = joblib.load("models/risk_model.joblib")
        cls.health_model = joblib.load("models/health_model.joblib")
        cls.distress_model = joblib.load("models/distress_model.joblib")

    def test_single_inference_pipeline(self):
        sample_client = {
            "age": 35,
            "annual_income": 95000.0,
            "monthly_expenses": 3800.0,
            "dependents": 2,
            "credit_score": 750,
            "total_debt": 20000.0,
            "monthly_debt_payment": 450.0,
            "current_savings": 30000.0,
            "current_investments": 60000.0,
            "investment_horizon": 20
        }

        scaled, ratios = self.preprocessor.preprocess_single(sample_client)
        
        # Check scaled shape
        self.assertEqual(scaled.shape, (1, 16))
        
        # Check derived ratios
        self.assertGreater(ratios["emergency_months"], 0)
        self.assertGreater(ratios["savings_rate"], -1.0)
        self.assertGreater(ratios["net_worth"], 0)

        # Predict Risk
        risk_pred = self.risk_model.predict(scaled)[0]
        self.assertIn(risk_pred, ["Conservative", "Moderate", "Balanced", "Aggressive"])

        # Predict Health Score
        health_pred = float(self.health_model.predict(scaled)[0])
        self.assertGreaterEqual(health_pred, 0.0)
        self.assertLessEqual(health_pred, 100.0)

        # Predict Distress
        distress_prob = float(self.distress_model.predict_proba(scaled)[0][1])
        self.assertGreaterEqual(distress_prob, 0.0)
        self.assertLessEqual(distress_prob, 1.0)

if __name__ == "__main__":
    unittest.main()
