"""
FinPulse AI - UI Styling, Formatters, and Validation Utilities
Provides dark glassmorphism CSS injection, numeric formatters, and exportable reports.
"""

import streamlit as st
from typing import Dict, Any

def inject_custom_css():
    st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        max-width: 1240px;
    }

    /* Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.45);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #F9FAFB;
        line-height: 1.2;
    }
    .metric-delta {
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 0.35rem;
    }
    .delta-positive { color: #10B981; }
    .delta-neutral { color: #3B82F6; }
    .delta-negative { color: #EF4444; }

    /* Custom Badges */
    .badge {
        display: inline-block;
        padding: 0.28rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-blue { background: rgba(59, 130, 246, 0.18); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-green { background: rgba(16, 185, 129, 0.18); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-yellow { background: rgba(245, 158, 11, 0.18); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-red { background: rgba(239, 68, 68, 0.18); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }

    /* Modern Card Containers */
    .fin-card {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0E1424;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #1F2937;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
        color: #9CA3AF;
        padding: 8px 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1F2937 !important;
        color: #3B82F6 !important;
    }

    /* Streamlit Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: #FFFFFF;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 1.25rem;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)

def format_currency(val: float) -> str:
    if val >= 1_000_000:
        return f"${val/1_000_000:.2f}M"
    elif val >= 10_000:
        return f"${val:,.0f}"
    else:
        return f"${val:,.2f}"

def format_pct(val: float) -> str:
    return f"{val:.1f}%"

def generate_advisory_pdf_text(profile: Dict[str, Any], ratios: Dict[str, Any], allocation: Dict[str, Any]) -> str:
    report = f"""# FinPulse AI - Personalized Comprehensive Wealth & Advisory Report
**Generated On**: Automatic AI Diagnosis Session
**Client Name**: {profile.get('full_name', 'Valued Client')}
**Age**: {profile.get('age', 30)} | **Investment Horizon**: {profile.get('investment_horizon', 15)} Years

---

## 1. Executive Financial Health Summary
- **AI Health Index**: {profile.get('health_score', 75):.1f} / 100
- **AI Diagnosed Risk Appetite**: {profile.get('risk_profile', 'Balanced')}
- **Calculated Net Worth**: ${ratios.get('net_worth', 0):,.2f}
- **Savings Rate**: {ratios.get('savings_rate', 0)*100:.1f}% (Industry Benchmark: 15% - 20%)
- **Debt-to-Income (DTI)**: {ratios.get('dti_ratio', 0)*100:.1f}% (Healthy Threshold: <36%)
- **Emergency Reserve Cushion**: {ratios.get('emergency_months', 0):.1f} Months of Living Expenses

---

## 2. Optimized Strategic Asset Allocation
Based on Modern Portfolio Theory (MPT) and your AI-diagnosed {profile.get('risk_profile', 'Balanced')} profile:
- **Expected Annualized Return**: {allocation.get('expected_annual_return', 7.5)}%
- **Portfolio Volatility**: {allocation.get('annual_volatility', 12.0)}%
- **Portfolio Sharpe Ratio**: {allocation.get('sharpe_ratio', 0.65)}

### Recommended Portfolio Weights:
"""
    for asset in allocation.get("allocation_breakdown", []):
        report += f"- **{asset['asset_name']}**: {asset['weight_pct']}% (Historical Exp Return: {asset['expected_return']}%, Volatility: {asset['volatility']}%)\n"

    report += """
---

## 3. Fiduciary Action Plan
1. **Liquidity Management**: Maintain at least 3-6 months in high-yield liquid cash before taking speculative exposure.
2. **Tax-Advantaged Compounding**: Prioritize employer 401(k) match, followed by HSA and Roth/Traditional IRA caps.
3. **Debt Optimization**: Direct excess free cash flow to any debts exceeding 7% APR using the Avalanche protocol.
4. **Automated DCA**: Execute consistent monthly dollar-cost averaging into low-cost, broadly diversified index ETFs.

---
*Disclaimer: FinPulse AI provides algorithmic data-driven financial modeling and planning information. Users should consult licensed financial advisors for complex legal or tax situations.*
"""
    return report
