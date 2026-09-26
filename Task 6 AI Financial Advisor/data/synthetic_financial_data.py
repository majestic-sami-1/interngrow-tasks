"""
FinPulse AI - Synthetic Financial Data Generator
Generates realistic client financial data incorporating demographic and economic distributions,
calculates standard financial ratios (DTI, Savings Rate, Liquidity Months, Net Worth),
and assigns ground-truth risk profiles and financial health indicators.
"""

import numpy as np
import pandas as pd
import os

def generate_financial_dataset(n_samples: int = 1500, random_state: int = 42) -> pd.DataFrame:
    np.random.seed(random_state)
    
    # 1. Demographics & Base Financials
    age = np.random.randint(21, 72, size=n_samples)
    
    # Income log-normal distribution to mirror realistic wealth skew
    income_base = np.random.lognormal(mean=11.1, sigma=0.55, size=n_samples)
    annual_income = np.clip(np.round(income_base, -2), 24000, 380000)
    
    # Dependents correlated with age
    dependents = np.where(age < 26, np.random.choice([0, 1], p=[0.85, 0.15], size=n_samples),
                 np.where(age < 50, np.random.choice([0, 1, 2, 3, 4], p=[0.25, 0.35, 0.25, 0.10, 0.05], size=n_samples),
                          np.random.choice([0, 1, 2], p=[0.60, 0.30, 0.10], size=n_samples)))
    
    # Monthly expenses roughly 40-75% of monthly income plus dependents factor
    monthly_income = annual_income / 12.0
    expense_ratio = np.random.uniform(0.38, 0.78, size=n_samples) + (dependents * 0.04)
    expense_ratio = np.clip(expense_ratio, 0.35, 0.92)
    monthly_expenses = np.round(monthly_income * expense_ratio, 2)
    
    # Credit Score (Beta distribution scaled to 480-850)
    credit_score = np.round(480 + np.random.beta(5, 2.5, size=n_samples) * 370).astype(int)
    credit_score = np.clip(credit_score, 500, 850)
    
    # Debt: Correlated inversely with credit score and varied by income
    has_debt = np.random.choice([1, 0], p=[0.72, 0.28], size=n_samples)
    debt_multiplier = np.random.uniform(0.1, 2.8, size=n_samples)
    total_debt = np.where(has_debt == 1, np.round(annual_income * debt_multiplier * (900 - credit_score) / 400, -2), 0.0)
    total_debt = np.clip(total_debt, 0, 450000)
    
    # Monthly debt payment approx 1.5% to 3.5% of total debt
    monthly_debt_payment = np.where(total_debt > 0, np.round(total_debt * np.random.uniform(0.015, 0.032, size=n_samples), 2), 0.0)
    
    # Savings & Liquid Assets
    # Older and higher credit score clients tend to have higher accumulated assets
    savings_years_factor = np.clip((age - 20) / 35.0, 0.1, 1.5)
    savings_base = annual_income * savings_years_factor * np.random.uniform(0.1, 1.2, size=n_samples)
    current_savings = np.clip(np.round(savings_base * (credit_score / 750), -2), 500, 450000)
    
    # Investments (Stocks, Bonds, Mutual Funds)
    invest_propensity = np.clip((age - 22) * 0.02 + (annual_income / 150000) * 0.4, 0.05, 0.95)
    has_investments = (np.random.uniform(0, 1, size=n_samples) < invest_propensity).astype(int)
    current_investments = np.where(has_investments == 1, 
                                   np.round(current_savings * np.random.uniform(0.5, 3.5, size=n_samples), -2), 
                                   0.0)
    
    # Investment Horizon (Retirement age ~65 minus current age or target goal)
    investment_horizon = np.clip(67 - age + np.random.randint(-3, 6, size=n_samples), 2, 40)
    
    # 2. Key Engineered Financial Ratios
    # Debt-to-Income (DTI)
    dti_ratio = np.clip(np.round((monthly_debt_payment * 12.0) / annual_income, 4), 0.0, 0.95)
    
    # Savings Rate: portion of income saved after expenses and debt
    disposable_monthly = monthly_income - monthly_expenses - monthly_debt_payment
    savings_rate = np.clip(np.round(disposable_monthly / monthly_income, 4), -0.20, 0.65)
    
    # Emergency Fund Coverage (Months of expenses covered by liquid savings)
    emergency_months = np.clip(np.round(current_savings / np.maximum(monthly_expenses, 1.0), 2), 0.1, 36.0)
    
    # Net Worth
    net_worth = np.round(current_savings + current_investments - total_debt, 2)
    
    # 3. Ground Truth Labels Generation
    
    # (A) Financial Health Score (Composite 0 - 100)
    # Rationale: high savings rate (+), high credit score (+), adequate emergency fund (+), low DTI (+)
    health_raw = (
        (np.clip(savings_rate, 0, 0.4) / 0.4) * 30.0 +
        ((credit_score - 500) / 350.0) * 25.0 +
        (np.clip(emergency_months, 0, 9) / 9.0) * 25.0 +
        (np.clip(1.0 - (dti_ratio / 0.5), 0, 1.0)) * 20.0
    )
    financial_health_score = np.clip(np.round(health_raw, 1), 5.0, 99.0)
    
    # (B) Financial Distress Risk (Binary: 1 = Distress/Vulnerable, 0 = Stable)
    # Defined by: DTI > 0.45 or emergency_months < 1.5 with negative savings rate or credit score < 580
    distress_condition = (
        (dti_ratio > 0.42) | 
        ((emergency_months < 1.8) & (savings_rate <= 0.02)) | 
        (credit_score < 570)
    )
    distress_risk = distress_condition.astype(int)
    
    # (C) Risk Tolerance / Appetite Classifier
    # Financial capacity + psychological willingness (influenced by horizon, age, emergency cushion, DTI)
    risk_score_calc = (
        (investment_horizon / 40.0) * 35.0 +
        (np.clip(emergency_months, 0, 12) / 12.0) * 25.0 +
        (np.clip(1.0 - dti_ratio, 0, 1.0)) * 20.0 +
        (np.clip((75 - age) / 50.0, 0, 1.0)) * 20.0
    )
    
    # Add random investor behavior noise
    risk_score_calc += np.random.normal(0, 7.5, size=n_samples)
    
    risk_profiles = []
    for score in risk_score_calc:
        if score < 42:
            risk_profiles.append("Conservative")
        elif score < 60:
            risk_profiles.append("Moderate")
        elif score < 76:
            risk_profiles.append("Balanced")
        else:
            risk_profiles.append("Aggressive")
            
    df = pd.DataFrame({
        "age": age,
        "annual_income": annual_income,
        "monthly_expenses": monthly_expenses,
        "dependents": dependents,
        "credit_score": credit_score,
        "total_debt": total_debt,
        "monthly_debt_payment": monthly_debt_payment,
        "current_savings": current_savings,
        "current_investments": current_investments,
        "investment_horizon": investment_horizon,
        "dti_ratio": dti_ratio,
        "savings_rate": savings_rate,
        "emergency_months": emergency_months,
        "net_worth": net_worth,
        "financial_health_score": financial_health_score,
        "distress_risk": distress_risk,
        "risk_profile": risk_profiles
    })
    
    return df

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df = generate_financial_dataset(n_samples=2000, random_state=42)
    output_path = os.path.join("data", "client_profiles.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic dataset with {len(df)} records saved to {output_path}")
    print("\nDataset Class Distribution for Risk Profile:")
    print(df["risk_profile"].value_counts(normalize=True))
    print("\nDataset Distress Risk Distribution:")
    print(df["distress_risk"].value_counts(normalize=True))
