"""
Unit tests for financial calculations, MPT allocations, and Monte Carlo engine.
"""

import unittest
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.finance_engine import (
    get_recommended_allocation, generate_efficient_frontier,
    run_monte_carlo_simulation, calculate_fire_metrics
)

class TestFinanceEngine(unittest.TestCase):
    def test_asset_allocation(self):
        for profile in ["Conservative", "Moderate", "Balanced", "Aggressive"]:
            alloc = get_recommended_allocation(profile)
            self.assertEqual(alloc["risk_profile"], profile)
            self.assertGreater(alloc["expected_annual_return"], 3.0)
            self.assertGreater(alloc["annual_volatility"], 1.0)
            self.assertGreater(alloc["sharpe_ratio"], 0.0)
            
            # Check sum of weights
            total_w = sum(a["weight_pct"] for a in alloc["allocation_breakdown"])
            self.assertAlmostEqual(total_w, 100.0, delta=1.0)

    def test_efficient_frontier_generation(self):
        df_frontier = generate_efficient_frontier(n_simulations=50)
        self.assertEqual(len(df_frontier), 50)
        self.assertIn("volatility", df_frontier.columns)
        self.assertIn("return", df_frontier.columns)
        self.assertIn("sharpe", df_frontier.columns)

    def test_monte_carlo_simulation(self):
        mc = run_monte_carlo_simulation(
            initial_wealth=10000.0,
            monthly_contribution=500.0,
            annual_return=0.08,
            annual_volatility=0.12,
            years=10,
            n_simulations=100
        )
        self.assertIn("final_median", mc)
        self.assertIn("projection_df", mc)
        self.assertGreater(mc["final_median"], mc["final_p10"])
        self.assertGreater(mc["final_p90"], mc["final_median"])
        self.assertEqual(len(mc["projection_df"]), 11)  # Year 0 to 10

    def test_fire_metrics(self):
        fire = calculate_fire_metrics(annual_expenses=40000.0, current_net_worth=200000.0, annual_savings=15000.0)
        self.assertEqual(fire["fire_target"], 1000000.0)  # 40000 * 25
        self.assertEqual(fire["current_funding_pct"], 20.0)  # 200000 / 1000000 * 100
        self.assertGreater(fire["years_to_fire"], 0)

if __name__ == "__main__":
    unittest.main()
