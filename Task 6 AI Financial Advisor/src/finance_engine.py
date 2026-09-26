"""
FinPulse AI - Financial Calculation & Algorithmic Modeling Engine
Features:
1. Modern Portfolio Theory (MPT) & Efficient Frontier Optimization
2. Monte Carlo Wealth Simulation (1,000 stochastic trajectories)
3. Debt Repayment Optimization (Avalanche vs. Snowball)
4. FIRE & Retirement Runway Projection
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

# Asset Class Definitions with historical annualized return & volatility benchmarks
ASSET_CLASSES = {
    "us_equities": {"name": "US Large-Cap Equity", "return": 0.102, "volatility": 0.155},
    "global_equities": {"name": "International Equity", "return": 0.082, "volatility": 0.170},
    "fixed_income": {"name": "Core Bonds & Treasuries", "return": 0.045, "volatility": 0.055},
    "real_assets": {"name": "Real Estate & Commodities", "return": 0.075, "volatility": 0.140},
    "cash_equivalents": {"name": "High-Yield Cash / T-Bills", "return": 0.038, "volatility": 0.012}
}

# Correlation Matrix between assets
CORR_MATRIX = np.array([
    [1.00, 0.78, 0.12, 0.55, 0.05],  # us_equities
    [0.78, 1.00, 0.15, 0.60, 0.02],  # global_equities
    [0.12, 0.15, 1.00, 0.20, 0.18],  # fixed_income
    [0.55, 0.60, 0.20, 1.00, 0.08],  # real_assets
    [0.05, 0.02, 0.18, 0.08, 1.00]   # cash_equivalents
])

RISK_FREE_RATE = 0.040  # 4.0% baseline risk-free rate

TARGET_ALLOCATIONS = {
    "Conservative": {
        "us_equities": 0.15,
        "global_equities": 0.05,
        "fixed_income": 0.50,
        "real_assets": 0.05,
        "cash_equivalents": 0.25
    },
    "Moderate": {
        "us_equities": 0.35,
        "global_equities": 0.15,
        "fixed_income": 0.35,
        "real_assets": 0.05,
        "cash_equivalents": 0.10
    },
    "Balanced": {
        "us_equities": 0.45,
        "global_equities": 0.25,
        "fixed_income": 0.20,
        "real_assets": 0.05,
        "cash_equivalents": 0.05
    },
    "Aggressive": {
        "us_equities": 0.60,
        "global_equities": 0.30,
        "fixed_income": 0.05,
        "real_assets": 0.05,
        "cash_equivalents": 0.00
    }
}

def get_asset_stats():
    keys = list(ASSET_CLASSES.keys())
    returns = np.array([ASSET_CLASSES[k]["return"] for k in keys])
    vols = np.array([ASSET_CLASSES[k]["volatility"] for k in keys])
    cov_matrix = np.outer(vols, vols) * CORR_MATRIX
    return keys, returns, vols, cov_matrix

def calculate_portfolio_metrics(weights: np.ndarray) -> Tuple[float, float, float]:
    _, returns, _, cov_matrix = get_asset_stats()
    w = np.array(weights)
    port_return = float(np.dot(w, returns))
    port_vol = float(np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))))
    sharpe = float((port_return - RISK_FREE_RATE) / port_vol) if port_vol > 0 else 0.0
    return port_return, port_vol, sharpe

def get_recommended_allocation(risk_profile: str) -> Dict[str, Any]:
    norm_profile = risk_profile.capitalize() if risk_profile else "Balanced"
    if norm_profile not in TARGET_ALLOCATIONS:
        norm_profile = "Balanced"
        
    weights_dict = TARGET_ALLOCATIONS[norm_profile]
    weights_vec = [weights_dict[k] for k in ASSET_CLASSES.keys()]
    exp_return, volatility, sharpe = calculate_portfolio_metrics(np.array(weights_vec))
    
    breakdown = []
    for k, w in weights_dict.items():
        breakdown.append({
            "asset_code": k,
            "asset_name": ASSET_CLASSES[k]["name"],
            "weight_pct": round(w * 100, 1),
            "expected_return": round(ASSET_CLASSES[k]["return"] * 100, 2),
            "volatility": round(ASSET_CLASSES[k]["volatility"] * 100, 2)
        })
        
    return {
        "risk_profile": norm_profile,
        "expected_annual_return": round(exp_return * 100, 2),
        "annual_volatility": round(volatility * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "allocation_breakdown": breakdown,
        "weights_dict": weights_dict
    }

def generate_efficient_frontier(n_simulations: int = 400) -> pd.DataFrame:
    np.random.seed(42)
    keys, returns, _, cov_matrix = get_asset_stats()
    n_assets = len(keys)
    
    results = []
    for _ in range(n_simulations):
        weights = np.random.random(n_assets)
        weights /= np.sum(weights)
        
        p_ret = np.dot(weights, returns)
        p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        p_sharpe = (p_ret - RISK_FREE_RATE) / p_vol
        
        row = {
            "volatility": round(float(p_vol) * 100, 2),
            "return": round(float(p_ret) * 100, 2),
            "sharpe": round(float(p_sharpe), 3)
        }
        for i, k in enumerate(keys):
            row[k] = round(float(weights[i]) * 100, 1)
        results.append(row)
        
    df_frontier = pd.DataFrame(results)
    return df_frontier

def run_monte_carlo_simulation(
    initial_wealth: float,
    monthly_contribution: float,
    annual_return: float,
    annual_volatility: float,
    years: int = 20,
    n_simulations: int = 1000,
    inflation_rate: float = 0.025
) -> Dict[str, Any]:
    """
    Simulates monthly portfolio values via geometric Brownian motion with continuous contributions.
    """
    np.random.seed(42)
    months = years * 12
    monthly_mean = (annual_return - inflation_rate) / 12.0
    monthly_vol = annual_volatility / np.sqrt(12.0)
    
    # Initialize trajectories matrix (n_simulations, months + 1)
    trajectories = np.zeros((n_simulations, months + 1))
    trajectories[:, 0] = max(initial_wealth, 100.0)
    
    # Random shocks
    shocks = np.random.normal(monthly_mean - 0.5 * (monthly_vol ** 2), monthly_vol, size=(n_simulations, months))
    
    for t in range(1, months + 1):
        growth = np.exp(shocks[:, t - 1])
        trajectories[:, t] = trajectories[:, t - 1] * growth + monthly_contribution
        trajectories[:, t] = np.maximum(trajectories[:, t], 0.0)
        
    year_indices = [y * 12 for y in range(years + 1)]
    yearly_trajectories = trajectories[:, year_indices]
    
    # Percentiles
    p10 = np.percentile(yearly_trajectories, 10, axis=0)
    p50 = np.percentile(yearly_trajectories, 50, axis=0)
    p90 = np.percentile(yearly_trajectories, 90, axis=0)
    
    final_median = float(p50[-1])
    final_p10 = float(p10[-1])
    final_p90 = float(p90[-1])
    total_contributed = initial_wealth + (monthly_contribution * months)
    
    projection_df = pd.DataFrame({
        "year": list(range(years + 1)),
        "p10_bear": np.round(p10, 0),
        "p50_median": np.round(p50, 0),
        "p90_bull": np.round(p90, 0),
        "total_principal": np.round([initial_wealth + (monthly_contribution * y * 12) for y in range(years + 1)], 0)
    })
    
    return {
        "projection_df": projection_df,
        "final_median": final_median,
        "final_p10": final_p10,
        "final_p90": final_p90,
        "total_contributed": total_contributed,
        "estimated_growth": max(0.0, final_median - total_contributed)
    }

def calculate_fire_metrics(annual_expenses: float, current_net_worth: float, annual_savings: float, return_rate: float = 0.07) -> Dict[str, Any]:
    """Calculates Financial Independence Retire Early (FIRE) milestones based on the 4% rule."""
    fire_target = max(annual_expenses * 25.0, 100000.0)  # 25x annual expenses
    lean_fire = max(annual_expenses * 0.75 * 25.0, 75000.0)
    fat_fire = max(annual_expenses * 1.35 * 25.0, 135000.0)
    
    current_funding_pct = min(100.0, (max(current_net_worth, 0) / fire_target) * 100.0)
    
    # Estimate years to FIRE
    years_to_fire = 0
    sim_wealth = max(current_net_worth, 0)
    if sim_wealth >= fire_target:
        years_to_fire = 0
    elif annual_savings <= 0:
        years_to_fire = 99
    else:
        for y in range(1, 60):
            sim_wealth = (sim_wealth * (1 + return_rate)) + annual_savings
            if sim_wealth >= fire_target:
                years_to_fire = y
                break
        else:
            years_to_fire = 60
            
    return {
        "fire_target": round(fire_target, 0),
        "lean_fire": round(lean_fire, 0),
        "fat_fire": round(fat_fire, 0),
        "current_funding_pct": round(current_funding_pct, 1),
        "years_to_fire": years_to_fire
    }
