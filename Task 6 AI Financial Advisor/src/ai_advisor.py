"""
FinPulse AI - Intelligent Financial Advisor & Strategic Synthesis Engine
Features:
1. Deterministic Multi-Pillar Financial Reasoning Engine
2. Optional API-Based LLM Integration (OpenAI / Groq / Gemini compatible)
3. Actionable Milestone & Roadmap Generator
4. Comprehensive Advisory Report Synthesis
"""

import os
import requests
from typing import Dict, Any, List

def generate_financial_diagnosis(profile: Dict[str, Any], ratios: Dict[str, Any]) -> Dict[str, Any]:
    """Generates structured financial diagnosis based on quantitative ratios and profile."""
    dti = ratios.get("dti_ratio", 0.20)
    savings_rate = ratios.get("savings_rate", 0.15)
    emergency_months = ratios.get("emergency_months", 3.0)
    net_worth = ratios.get("net_worth", 50000.0)
    credit_score = profile.get("credit_score", 720)
    risk_profile = profile.get("risk_profile", "Balanced")
    
    strengths = []
    vulnerabilities = []
    action_steps = []
    
    # Emergency Fund Pillar
    if emergency_months >= 6.0:
        strengths.append(f"Strong liquidity cushion: {emergency_months:.1f} months of expenses saved (recommended 3-6 months).")
    elif emergency_months >= 3.0:
        strengths.append(f"Adequate emergency reserve: {emergency_months:.1f} months covered.")
    else:
        vulnerabilities.append(f"Vulnerable liquidity: Only {emergency_months:.1f} months of expenses in cash. Unforeseen expenses may force high-interest debt.")
        action_steps.append(f"Priority 1: Build liquid emergency fund to at least 3 months (${profile.get('monthly_expenses', 3000) * 3:,.0f}).")
        
    # Debt & DTI Pillar
    if dti > 0.40:
        vulnerabilities.append(f"High Debt-to-Income ratio ({dti*100:.1f}%). Lenders view ratios above 36-43% as elevated risk.")
        action_steps.append("Adopt the Debt Avalanche protocol: funnel all surplus cash into highest interest rate liabilities first.")
    elif dti > 0.20:
        strengths.append(f"Manageable debt burden: DTI is {dti*100:.1f}%.")
    else:
        strengths.append(f"Exceptional debt control: DTI is only {dti*100:.1f}%, leaving ample disposable income.")
        
    # Savings Rate Pillar
    if savings_rate >= 0.25:
        strengths.append(f"Elite savings rate of {savings_rate*100:.1f}%. You are on an accelerated wealth accumulation trajectory.")
    elif savings_rate >= 0.15:
        strengths.append(f"Healthy savings rate of {savings_rate*100:.1f}%, aligning with standard financial independence benchmarks.")
    elif savings_rate > 0:
        vulnerabilities.append(f"Modest savings rate ({savings_rate*100:.1f}%). Compounding returns require a minimum 15-20% target.")
        action_steps.append("Audit recurring monthly subscriptions and discretionary expenditures to target a 15%+ savings rate.")
    else:
        vulnerabilities.append("Negative cash flow: Monthly spending and debt obligations exceed income.")
        action_steps.append("Urgent cash flow restructuring needed: Trim non-essential expenses to eliminate monthly deficit.")
        
    # Credit Score Pillar
    if credit_score >= 740:
        strengths.append(f"Excellent credit score ({credit_score}), qualifying you for prime borrowing and mortgage rates.")
    elif credit_score < 620:
        vulnerabilities.append(f"Subprime credit score ({credit_score}), which significantly inflates borrowing costs.")
        action_steps.append("Keep credit card utilization below 30% and ensure zero late payments to elevate credit tier.")

    # Investment Strategy Pillar
    action_steps.append(f"Align portfolio with your AI-diagnosed {risk_profile} risk tolerance: Automate dollar-cost averaging into diversified index funds.")
    
    return {
        "strengths": strengths,
        "vulnerabilities": vulnerabilities,
        "action_steps": action_steps,
        "health_summary": f"Your financial profile indicates a {risk_profile} investment horizon with a net worth of ${net_worth:,.0f}."
    }

def get_ai_advisor_response(
    user_query: str,
    profile: Dict[str, Any],
    ratios: Dict[str, Any],
    api_key: str = "",
    chat_history: List[Dict[str, str]] = None
) -> str:
    """
    Synthesizes AI advisory response. Uses external LLM API if valid API key is supplied,
    otherwise uses FinPulse AI's specialized financial reasoning engine.
    """
    user_query_lower = user_query.lower()
    diagnosis = generate_financial_diagnosis(profile, ratios)
    
    # Check if API key is provided and try LLM call
    if api_key and len(api_key.strip()) > 15:
        try:
            prompt_system = f"""You are FinPulse AI, a certified fiduciary financial advisor and quantitative wealth strategist.
Client Financial Context:
- Age: {profile.get('age', 32)}
- Annual Income: ${profile.get('annual_income', 75000):,.0f}
- Monthly Expenses: ${profile.get('monthly_expenses', 3500):,.0f}
- Total Debt: ${profile.get('total_debt', 15000):,.0f}
- Current Savings: ${profile.get('current_savings', 20000):,.0f}
- Current Investments: ${profile.get('current_investments', 40000):,.0f}
- Net Worth: ${ratios.get('net_worth', 45000):,.0f}
- Risk Profile: {profile.get('risk_profile', 'Balanced')}
- Emergency Cushion: {ratios.get('emergency_months', 4):.1f} months
- Savings Rate: {ratios.get('savings_rate', 0.18)*100:.1f}%
- DTI Ratio: {ratios.get('dti_ratio', 0.2)*100:.1f}%

Give structured, practical, empowering financial advice. Use bullet points and clear numbers."""

            messages = [{"role": "system", "content": prompt_system}]
            if chat_history:
                for msg in chat_history[-4:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_query})
            
            headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 700
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            pass  # Fall back gracefully to internal reasoning engine

    # Internal Financial Reasoning Engine
    advice_sections = []
    
    if any(k in user_query_lower for k in ["debt", "loan", "pay off", "credit card", "avalanche", "snowball"]):
        advice_sections.append(f"""### 💳 Strategic Debt Elimination Blueprint
- **Current Debt Burden**: ${profile.get('total_debt', 0):,.0f} with monthly service of ${profile.get('monthly_debt_payment', 0):,.0f} (DTI: {ratios.get('dti_ratio', 0.2)*100:.1f}%).
- **Recommended Method**: **Debt Avalanche**. Rank debts by interest rate from highest to lowest. Pay minimum balances on all except the highest APR debt, directing every extra dollar to it.
- **Immediate Win**: Refinance high-rate consumer balances (>18%) into lower fixed consolidation loans or zero-interest transfer offers if credit score permits ({profile.get('credit_score', 700)}).""")

    elif any(k in user_query_lower for k in ["invest", "portfolio", "stock", "etf", "allocation", "crypto", "return"]):
        advice_sections.append(f"""### 📈 Portfolio & Asset Optimization Strategy
- **Risk Profile**: **{profile.get('risk_profile', 'Balanced')}** (Diagnosed by AI Classifier).
- **Target Allocation Strategy**:
  - **Core Equities (60-70%)**: Broad market total stock index (e.g. S&P 500 / Total World Stock) for compounding capital appreciation.
  - **Fixed Income (15-25%)**: Government & short-term investment-grade corporate bonds for capital preservation and volatility buffering.
  - **Liquid Buffer (5-10%)**: High-yield cash / money market earning risk-free yields.
- **Execution Rule**: Automate bi-weekly dollar-cost averaging (DCA) to remove market timing emotion.""")

    elif any(k in user_query_lower for k in ["emergency", "cushion", "liquidity", "safe"]):
        advice_sections.append(f"""### 🛡️ Emergency Reserve & Capital Protection
- **Current Coverage**: **{ratios.get('emergency_months', 3):.1f} Months** of living expenses (${profile.get('current_savings', 10000):,.0f}).
- **Benchmark**: For a household with {profile.get('dependents', 0)} dependent(s), a minimum of **3 to 6 months** (${profile.get('monthly_expenses', 3000)*4:,.0f}) is required.
- **Storage**: Store emergency funds strictly in FDIC-insured High-Yield Savings Accounts (HYSA) or Treasury Bills.""")

    elif any(k in user_query_lower for k in ["retire", "fire", "pension", "401k", "ira", "freedom"]):
        exp = profile.get("monthly_expenses", 3500) * 12
        fire_num = exp * 25
        advice_sections.append(f"""### 🏖️ Retirement & Financial Independence (FIRE)
- **Annual Living Expense**: ${exp:,.0f}
- **Target Financial Independence Number (4% Rule)**: **${fire_num:,.0f}**
- **Action Step**: Maximize tax-advantaged accounts sequentially:
  1. 401(k) up to employer match (100% risk-free return).
  2. HSA (triple-tax advantage).
  3. Roth / Traditional IRA up to statutory annual cap.
  4. Taxable brokerage for surplus index funds.""")

    else:
        advice_sections.append(f"""### 🎯 FinPulse AI Executive Financial Advisory
Here is your tailored strategic assessment based on your current metrics:

**1. Key Financial Health Strengths:**
""" + "\n".join([f"- ✅ {s}" for s in diagnosis["strengths"]]) + f"""

**2. Key Opportunities & Vulnerabilities:**
""" + "\n".join([f"- ⚠️ {v}" for v in diagnosis["vulnerabilities"]]) + f"""

**3. Next Tactical Action Steps:**
""" + "\n".join([f"- 📌 {a}" for a in diagnosis["action_steps"]]))

    return "\n\n".join(advice_sections)
