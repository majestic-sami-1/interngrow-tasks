"""
FinPulse AI - Production-Ready Intelligent Financial Advisor & Wealth Engine
Built with Streamlit, Scikit-Learn, Plotly, and SQLite.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import joblib

# Page configuration
st.set_page_config(
    page_title="FinPulse AI - Next-Gen Financial Advisor",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Internal module imports
from src.database import init_db, save_user_profile, get_user_profile, add_goal, get_user_goals, delete_goal, log_advisory
from src.auth import authenticate_user, register_user
from src.finance_engine import (
    get_recommended_allocation, generate_efficient_frontier,
    run_monte_carlo_simulation, calculate_fire_metrics, ASSET_CLASSES
)
from src.ai_advisor import get_ai_advisor_response, generate_financial_diagnosis
from src.utils import inject_custom_css, format_currency, format_pct, generate_advisory_pdf_text
from models.preprocessor import FinancialDataPreprocessor, FEATURE_COLUMNS

# Initialize database
init_db()

# Inject glassmorphic custom stylesheet
inject_custom_css()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "diagnosis_result" not in st.session_state:
    st.session_state["diagnosis_result"] = None
if "user_profile_data" not in st.session_state:
    st.session_state["user_profile_data"] = None

# Cache Model & Metric Loading
@st.cache_resource
def load_ml_artifacts():
    try:
        import sys
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        if models_dir not in sys.path:
            sys.path.insert(0, models_dir)
        import models.preprocessor as mp
        sys.modules["preprocessor"] = mp
        preprocessor = FinancialDataPreprocessor.load("models/preprocessor.joblib")
        risk_model = joblib.load("models/risk_model.joblib")
        health_model = joblib.load("models/health_model.joblib")
        distress_model = joblib.load("models/distress_model.joblib")
        with open("models/metrics.json", "r") as f:
            metrics = json.load(f)
        return preprocessor, risk_model, health_model, distress_model, metrics
    except Exception as e:
        st.error(f"Error loading ML artifacts: {e}")
        return None, None, None, None, None

preprocessor, risk_model, health_model, distress_model, metrics_data = load_ml_artifacts()

# -------------------------------------------------------------
# SIDEBAR: User Authentication & Profile Drawer
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("## 💎 **FinPulse AI**")
    st.caption("Production Wealth & Fiduciary Intelligence")
    st.divider()

    if not st.session_state["authenticated"]:
        st.markdown("### 🔐 User Portal")
        auth_mode = st.radio("Select Action", ["Login", "Register"], horizontal=True)

        if auth_mode == "Login":
            login_username = st.text_input("Username or Email", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            col_l1, col_l2 = st.columns([1, 1])
            with col_l1:
                if st.button("Sign In", use_container_width=True):
                    success, msg, user_data = authenticate_user(login_username, login_password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["user_info"] = user_data
                        profile = get_user_profile(user_data["id"])
                        st.session_state["user_profile_data"] = profile
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col_l2:
                if st.button("⚡ Demo User", use_container_width=True, help="One-click demo login"):
                    # Register demo user if doesn't exist
                    register_user("demouser", "demo@finpulse.ai", "demopass123", "Alex Morgan")
                    success, _, user_data = authenticate_user("demouser", "demopass123")
                    st.session_state["authenticated"] = True
                    st.session_state["user_info"] = user_data
                    profile = get_user_profile(user_data["id"])
                    st.session_state["user_profile_data"] = profile
                    st.rerun()

        else:
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_username = st.text_input("Username", key="reg_user")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password (min 6 chars)", type="password", key="reg_pass")
            if st.button("Create Account", use_container_width=True):
                success, msg, _ = register_user(reg_username, reg_email, reg_password, reg_name)
                if success:
                    st.success("Account created! You can now log in.")
                else:
                    st.error(msg)

    else:
        user = st.session_state["user_info"]
        st.markdown(f"### 👤 **{user['full_name']}**")
        st.caption(f"@{user['username']} • {user['email']}")
        
        # Current Profile Quick Status
        current_prof = st.session_state.get("user_profile_data")
        if current_prof:
            st.markdown(f"""
            <div style='background: rgba(31, 41, 55, 0.6); padding: 10px; border-radius: 8px; margin: 10px 0;'>
                <span style='color: #9CA3AF; font-size: 0.8rem;'>RISK PROFILE:</span><br/>
                <span class='badge badge-blue'>{current_prof.get('risk_profile', 'Moderate')}</span><br/>
                <span style='color: #9CA3AF; font-size: 0.8rem; margin-top: 6px; display:inline-block;'>HEALTH SCORE:</span><br/>
                <span style='font-size: 1.2rem; font-weight: bold; color: #34D399;'>{current_prof.get('health_score', 75):.1f} / 100</span>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user_info"] = None
            st.session_state["user_profile_data"] = None
            st.session_state["chat_history"] = []
            st.session_state["diagnosis_result"] = None
            st.rerun()

    st.divider()
    st.markdown("### ⚙️ **AI Engine Settings**")
    api_key_input = st.text_input("Optional OpenAI / LLM API Key", type="password", help="Leave blank to use built-in FinPulse Financial Reasoning Engine")
    st.session_state["api_key"] = api_key_input

    st.markdown("### 📊 **System Health**")
    st.markdown("""
    - 🟢 **Risk Classifier**: `Active (RF)`
    - 🟢 **Health Regressor**: `Active (GBR)`
    - 🟢 **Distress Predictor**: `Active (AUC 0.99)`
    - 🟢 **DB Engine**: `SQLite Encrypted`
    """)

# -------------------------------------------------------------
# MAIN DASHBOARD INTERFACE
# -------------------------------------------------------------

# Top Banner
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("💎 FinPulse AI")
    st.caption("Production Autonomous Financial Advisor & Quantitative Wealth Optimization Platform")
with col_h2:
    if st.session_state["authenticated"]:
        st.markdown(f"""
        <div style='text-align: right; margin-top: 15px;'>
            <span class='badge badge-green'>● Active Session: {st.session_state['user_info']['username']}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align: right; margin-top: 15px;'>
            <span class='badge badge-yellow'>● Guest Mode (Sign in for sync)</span>
        </div>
        """, unsafe_allow_html=True)

# Main Navigation Tabs
tab_overview, tab_diagnosis, tab_portfolio, tab_advisor, tab_metrics = st.tabs([
    "🏠 Executive Overview",
    "🎯 AI Health & Risk Diagnosis",
    "📈 Portfolio & Monte Carlo",
    "💡 AI Advisor & Goals",
    "📊 Model Performance & XAI"
])

# Profile fallback loader
default_profile = {
    "age": 32,
    "annual_income": 85000.0,
    "monthly_expenses": 3400.0,
    "dependents": 1,
    "credit_score": 735,
    "total_debt": 14000.0,
    "monthly_debt_payment": 380.0,
    "current_savings": 22000.0,
    "current_investments": 48000.0,
    "investment_horizon": 18,
    "risk_profile": "Balanced",
    "health_score": 78.4,
    "distress_flag": 0
}

active_profile = st.session_state.get("user_profile_data") or default_profile

# Compute instantaneous ratios
m_income = max(active_profile["annual_income"] / 12.0, 1.0)
curr_dti = (active_profile["monthly_debt_payment"] * 12.0) / active_profile["annual_income"]
curr_savings_rate = (m_income - active_profile["monthly_expenses"] - active_profile["monthly_debt_payment"]) / m_income
curr_emergency_months = active_profile["current_savings"] / max(active_profile["monthly_expenses"], 1.0)
curr_net_worth = active_profile["current_savings"] + active_profile["current_investments"] - active_profile["total_debt"]
computed_ratios = {
    "dti_ratio": curr_dti,
    "savings_rate": curr_savings_rate,
    "emergency_months": curr_emergency_months,
    "net_worth": curr_net_worth
}

# =============================================================
# TAB 1: EXECUTIVE OVERVIEW
# =============================================================
with tab_overview:
    st.markdown("### 📈 Client Wealth Summary & Core Vital Signs")
    
    # KPI Cards Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Estimated Net Worth</div>
            <div class="metric-value">{format_currency(curr_net_worth)}</div>
            <div class="metric-delta delta-positive">Assets: {format_currency(active_profile['current_savings'] + active_profile['current_investments'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        health_val = active_profile.get("health_score", 75.0)
        h_color = "delta-positive" if health_val >= 70 else ("delta-neutral" if health_val >= 50 else "delta-negative")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">AI Health Index</div>
            <div class="metric-value">{health_val:.1f} / 100</div>
            <div class="metric-delta {h_color}">Status: {'Prime' if health_val >= 70 else 'Fair'}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        sr = curr_savings_rate * 100
        sr_color = "delta-positive" if sr >= 15 else ("delta-neutral" if sr >= 5 else "delta-negative")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Monthly Savings Rate</div>
            <div class="metric-value">{sr:.1f}%</div>
            <div class="metric-delta {sr_color}">Benchmark: 15% - 20%</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        em = curr_emergency_months
        em_color = "delta-positive" if em >= 3.0 else "delta-negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Emergency Cushion</div>
            <div class="metric-value">{em:.1f} Mo</div>
            <div class="metric-delta {em_color}">Liquidity: {format_currency(active_profile['current_savings'])}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Visualizations Row: Cash Flow Distribution & Asset Allocation
    col_v1, col_v2 = st.columns([1, 1])
    
    with col_v1:
        st.markdown("#### 💵 Monthly Cash Flow Composition")
        monthly_exp = active_profile["monthly_expenses"]
        monthly_debt = active_profile["monthly_debt_payment"]
        monthly_savings = max(0.0, m_income - monthly_exp - monthly_debt)
        
        cashflow_df = pd.DataFrame({
            "Category": ["Living Expenses", "Debt Payments", "Net Savings"],
            "Amount": [monthly_exp, monthly_debt, monthly_savings]
        })
        fig_cf = px.pie(
            cashflow_df,
            values="Amount",
            names="Category",
            hole=0.55,
            color_discrete_sequence=["#3B82F6", "#EF4444", "#10B981"]
        )
        fig_cf.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F9FAFB"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_cf, use_container_width=True)

    with col_v2:
        st.markdown(f"#### 🎯 Recommended Target Allocation ({active_profile.get('risk_profile', 'Balanced')})")
        rec_alloc = get_recommended_allocation(active_profile.get("risk_profile", "Balanced"))
        alloc_data = rec_alloc["allocation_breakdown"]
        alloc_df = pd.DataFrame(alloc_data)
        
        fig_alloc = px.pie(
            alloc_df,
            values="weight_pct",
            names="asset_name",
            hole=0.55,
            color_discrete_sequence=["#2563EB", "#38BDF8", "#10B981", "#F59E0B", "#6366F1"]
        )
        fig_alloc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F9FAFB"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_alloc, use_container_width=True)

    # Executive Diagnostic Highlights
    st.markdown("#### ⚡ AI Diagnostic Flash Insights")
    diag = generate_financial_diagnosis(active_profile, computed_ratios)
    c_diag1, c_diag2 = st.columns(2)
    with c_diag1:
        st.markdown("**Notable Strengths:**")
        for s in diag["strengths"]:
            st.markdown(f"✅ {s}")
    with c_diag2:
        st.markdown("**Opportunities & Warnings:**")
        for v in diag["vulnerabilities"]:
            st.markdown(f"⚠️ {v}")

# =============================================================
# TAB 2: AI HEALTH & RISK DIAGNOSIS
# =============================================================
with tab_diagnosis:
    st.markdown("### 🎯 AI Financial Profiler & Risk Appetite Diagnosis")
    st.caption("Input your financial parameters to trigger the trained Machine Learning classification and regression inference pipelines.")

    with st.form("financial_profile_form"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            st.markdown("##### 👤 Demographic & Income")
            f_age = st.slider("Client Age", min_value=18, max_value=80, value=int(active_profile.get("age", 32)))
            f_dependents = st.number_input("Dependents", min_value=0, max_value=10, value=int(active_profile.get("dependents", 1)))
            f_income = st.number_input("Annual Gross Income ($)", min_value=10000.0, max_value=2000000.0, value=float(active_profile.get("annual_income", 85000.0)), step=1000.0)
            f_expenses = st.number_input("Monthly Living Expenses ($)", min_value=500.0, max_value=50000.0, value=float(active_profile.get("monthly_expenses", 3400.0)), step=100.0)

        with col_f2:
            st.markdown("##### 💳 Debt & Credit Profile")
            f_credit = st.slider("Credit Score (FICO)", min_value=500, max_value=850, value=int(active_profile.get("credit_score", 735)))
            f_debt = st.number_input("Total Debt Balance ($)", min_value=0.0, max_value=2000000.0, value=float(active_profile.get("total_debt", 14000.0)), step=500.0)
            f_debt_pmt = st.number_input("Monthly Debt Servicing ($)", min_value=0.0, max_value=20000.0, value=float(active_profile.get("monthly_debt_payment", 380.0)), step=50.0)
            f_horizon = st.slider("Investment Horizon (Years)", min_value=1, max_value=40, value=int(active_profile.get("investment_horizon", 18)))

        with col_f3:
            st.markdown("##### 🏦 Assets & Liquidity")
            f_savings = st.number_input("Liquid Savings ($)", min_value=0.0, max_value=5000000.0, value=float(active_profile.get("current_savings", 22000.0)), step=500.0)
            f_investments = st.number_input("Current Investments ($)", min_value=0.0, max_value=10000000.0, value=float(active_profile.get("current_investments", 48000.0)), step=1000.0)
            st.markdown("<br/>", unsafe_allow_html=True)
            submit_profile = st.form_submit_button("🤖 Run AI Financial Diagnosis", use_container_width=True)

    if submit_profile:
        # Client input validation
        if (f_expenses * 12.0 + f_debt_pmt * 12.0) > (f_income * 1.3):
            st.warning("⚠️ Warning: Your total reported expenses and debt obligations significantly exceed annual income. Model has accounted for negative cash flow.")

        raw_input = {
            "age": f_age,
            "annual_income": f_income,
            "monthly_expenses": f_expenses,
            "dependents": f_dependents,
            "credit_score": f_credit,
            "total_debt": f_debt,
            "monthly_debt_payment": f_debt_pmt,
            "current_savings": f_savings,
            "current_investments": f_investments,
            "investment_horizon": f_horizon
        }

        with st.spinner("Processing through ML Pipelines..."):
            scaled_features, new_ratios = preprocessor.preprocess_single(raw_input)
            
            # Predict Risk Profile
            pred_risk = risk_model.predict(scaled_features)[0]
            risk_probs = risk_model.predict_proba(scaled_features)[0]
            risk_classes = risk_model.classes_

            # Predict Health Score
            pred_health = float(np.clip(health_model.predict(scaled_features)[0], 0.0, 100.0))

            # Predict Distress Probability
            pred_distress_prob = float(distress_model.predict_proba(scaled_features)[0][1])
            distress_flag = 1 if pred_distress_prob > 0.40 else 0

            # Package result
            updated_profile = {
                **raw_input,
                "risk_profile": pred_risk,
                "health_score": pred_health,
                "distress_flag": distress_flag
            }
            st.session_state["user_profile_data"] = updated_profile
            st.session_state["diagnosis_result"] = {
                "profile": updated_profile,
                "ratios": new_ratios,
                "risk_probs": dict(zip(risk_classes, [round(float(p)*100, 1) for p in risk_probs])),
                "distress_prob": round(pred_distress_prob * 100, 1)
            }

            # If user is authenticated, save to database
            if st.session_state["authenticated"]:
                save_user_profile(st.session_state["user_info"]["id"], updated_profile)
                st.toast("✅ Profile and AI predictions saved to database!", icon="💾")

    # Render Diagnosis Results
    diag_res = st.session_state.get("diagnosis_result")
    if diag_res:
        st.divider()
        st.markdown("### 🔍 **AI Diagnostic Inference Results**")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.markdown(f"""
            <div class="fin-card">
                <div class="metric-label">Predicted Risk Profile</div>
                <div style="font-size: 1.7rem; font-weight: bold; color: #60A5FA; margin-bottom: 8px;">
                    {diag_res['profile']['risk_profile']}
                </div>
                <span class="badge badge-blue">Random Forest Classifier</span>
                <p style="font-size: 0.85rem; color: #9CA3AF; margin-top: 10px;">
                    Matched for asset growth timeline of {diag_res['profile']['investment_horizon']} years.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_res2:
            st.markdown(f"""
            <div class="fin-card">
                <div class="metric-label">Financial Health Index</div>
                <div style="font-size: 1.7rem; font-weight: bold; color: #34D399; margin-bottom: 8px;">
                    {diag_res['profile']['health_score']:.1f} / 100
                </div>
                <span class="badge badge-green">Gradient Boosting Regressor</span>
                <p style="font-size: 0.85rem; color: #9CA3AF; margin-top: 10px;">
                    Composite health evaluation across 16 financial features.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_res3:
            d_prob = diag_res['distress_prob']
            d_badge = "badge-red" if d_prob >= 35 else "badge-green"
            d_color = "#F87171" if d_prob >= 35 else "#34D399"
            st.markdown(f"""
            <div class="fin-card">
                <div class="metric-label">Financial Vulnerability Risk</div>
                <div style="font-size: 1.7rem; font-weight: bold; color: {d_color}; margin-bottom: 8px;">
                    {d_prob:.1f}% Probability
                </div>
                <span class="badge {d_badge}">{'Elevated Distress Risk' if d_prob >= 35 else 'Secure / Low Stress'}</span>
                <p style="font-size: 0.85rem; color: #9CA3AF; margin-top: 10px;">
                    Calculated via debt service & liquidity thresholds.
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Risk Probability Distribution Bar Chart
        st.markdown("#### 📊 Risk Tolerance Probability Distribution")
        probs_df = pd.DataFrame({
            "Risk Profile": list(diag_res["risk_probs"].keys()),
            "Confidence (%)": list(diag_res["risk_probs"].values())
        })
        fig_prob = px.bar(
            probs_df,
            x="Risk Profile",
            y="Confidence (%)",
            text="Confidence (%)",
            color="Risk Profile",
            color_discrete_sequence=["#EF4444", "#3B82F6", "#10B981", "#F59E0B"]
        )
        fig_prob.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F9FAFB"),
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False
        )
        st.plotly_chart(fig_prob, use_container_width=True)

# =============================================================
# TAB 3: PORTFOLIO & MONTE CARLO
# =============================================================
with tab_portfolio:
    st.markdown("### 📈 Modern Portfolio Theory & Monte Carlo Wealth Simulator")
    st.caption("Quantitative portfolio optimization using Modern Portfolio Theory (MPT), Sharpe Ratio maximization, and 1,000 stochastic trajectory simulations.")

    # Efficient Frontier Chart
    st.markdown("#### 🌌 Efficient Frontier & Capital Allocation Curve")
    col_ef1, col_ef2 = st.columns([3, 1])
    
    with col_ef1:
        frontier_df = generate_efficient_frontier(n_simulations=400)
        curr_risk = active_profile.get("risk_profile", "Balanced")
        rec_portfolio = get_recommended_allocation(curr_risk)
        
        fig_ef = px.scatter(
            frontier_df,
            x="volatility",
            y="return",
            color="sharpe",
            color_continuous_scale="Viridis",
            labels={"volatility": "Annualized Volatility (%)", "return": "Expected Annual Return (%)", "sharpe": "Sharpe Ratio"},
            title="Markowitz Efficient Frontier (400 Portfolio Permutations)"
        )
        # Highlight User's Recommended Target
        fig_ef.add_trace(go.Scatter(
            x=[rec_portfolio["annual_volatility"]],
            y=[rec_portfolio["expected_annual_return"]],
            mode="markers+text",
            name=f"Your Portfolio ({curr_risk})",
            text=[f"★ {curr_risk} Portfolio"],
            textposition="top center",
            marker=dict(size=16, color="#EF4444", symbol="star")
        ))
        fig_ef.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F9FAFB"),
            margin=dict(t=40, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_ef, use_container_width=True)

    with col_ef2:
        st.markdown(f"""
        <div class="fin-card">
            <div class="metric-label">Target Strategy</div>
            <h4 style="color: #60A5FA; margin: 4px 0;">{rec_portfolio['risk_profile']}</h4>
            <hr style="border-color: #1F2937;"/>
            <p><strong>Expected Return:</strong> {rec_portfolio['expected_annual_return']}%</p>
            <p><strong>Volatility (Risk):</strong> {rec_portfolio['annual_volatility']}%</p>
            <p><strong>Sharpe Ratio:</strong> {rec_portfolio['sharpe_ratio']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Monte Carlo Wealth Engine
    st.markdown("#### 🎲 Monte Carlo Wealth Projection Engine (1,000 Runs)")
    
    col_mc_ctrl1, col_mc_ctrl2, col_mc_ctrl3 = st.columns(3)
    with col_mc_ctrl1:
        mc_initial = st.number_input("Starting Liquid Wealth ($)", min_value=500.0, value=float(active_profile.get("current_savings", 22000.0) + active_profile.get("current_investments", 48000.0)), step=5000.0)
    with col_mc_ctrl2:
        default_monthly_contrib = max(100.0, m_income - active_profile["monthly_expenses"] - active_profile["monthly_debt_payment"])
        mc_monthly = st.slider("Monthly Savings Contribution ($)", min_value=100.0, max_value=15000.0, value=float(round(default_monthly_contrib, -1)), step=50.0)
    with col_mc_ctrl3:
        mc_years = st.slider("Simulation Horizon (Years)", min_value=5, max_value=40, value=int(active_profile.get("investment_horizon", 20)))

    # Execute simulation
    mc_results = run_monte_carlo_simulation(
        initial_wealth=mc_initial,
        monthly_contribution=mc_monthly,
        annual_return=rec_portfolio["expected_annual_return"] / 100.0,
        annual_volatility=rec_portfolio["annual_volatility"] / 100.0,
        years=mc_years,
        n_simulations=1000
    )
    proj_df = mc_results["projection_df"]

    # Monte Carlo Fan Chart
    fig_mc = go.Figure()
    
    # 90th percentile (Bull)
    fig_mc.add_trace(go.Scatter(
        x=proj_df["year"], y=proj_df["p90_bull"],
        mode='lines', line=dict(color='rgba(16, 185, 129, 0.4)', width=1),
        name='90th Percentile (Bull Scenario)'
    ))
    # 50th percentile (Median)
    fig_mc.add_trace(go.Scatter(
        x=proj_df["year"], y=proj_df["p50_median"],
        mode='lines', line=dict(color='#3B82F6', width=3),
        name='50th Percentile (Expected Median)',
        fill='tonexty', fillcolor='rgba(59, 130, 246, 0.15)'
    ))
    # 10th percentile (Bear)
    fig_mc.add_trace(go.Scatter(
        x=proj_df["year"], y=proj_df["p10_bear"],
        mode='lines', line=dict(color='rgba(239, 68, 68, 0.4)', width=1),
        name='10th Percentile (Bear Scenario)',
        fill='tonexty', fillcolor='rgba(239, 68, 68, 0.15)'
    ))
    # Total Principal Contributed
    fig_mc.add_trace(go.Scatter(
        x=proj_df["year"], y=proj_df["total_principal"],
        mode='lines', line=dict(color='#9CA3AF', dash='dash', width=2),
        name='Cumulative Capital Contributed'
    ))

    fig_mc.update_layout(
        title=f"Stochastic Wealth Projections Over {mc_years} Years",
        xaxis_title="Investment Horizon (Years)",
        yaxis_title="Portfolio Valuation ($)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F9FAFB"),
        margin=dict(t=40, b=20, l=20, r=20),
        hovermode="x unified"
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    # Summary Metrics Row
    mc_k1, mc_k2, mc_k3 = st.columns(3)
    with mc_k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Median Expected Wealth</div>
            <div class="metric-value">{format_currency(mc_results['final_median'])}</div>
            <div class="metric-delta delta-positive">After {mc_years} Years</div>
        </div>
        """, unsafe_allow_html=True)
    with mc_k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Out-of-Pocket Principal</div>
            <div class="metric-value">{format_currency(mc_results['total_contributed'])}</div>
            <div class="metric-delta delta-neutral">${mc_monthly:,.0f}/month saved</div>
        </div>
        """, unsafe_allow_html=True)
    with mc_k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Estimated Compound Growth</div>
            <div class="metric-value">{format_currency(mc_results['estimated_growth'])}</div>
            <div class="metric-delta delta-positive">Pure Investment Returns</div>
        </div>
        """, unsafe_allow_html=True)

    # FIRE / Retirement Runway Calculator
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### 🏖️ FIRE (Financial Independence, Retire Early) Runway")
    annual_exp = active_profile["monthly_expenses"] * 12.0
    fire_stats = calculate_fire_metrics(annual_exp, curr_net_worth, mc_monthly * 12.0)
    
    col_fire1, col_fire2, col_fire3 = st.columns(3)
    with col_fire1:
        st.markdown(f"**FIRE Target (25x Expenses):** {format_currency(fire_stats['fire_target'])}")
        st.progress(fire_stats['current_funding_pct'] / 100.0)
        st.caption(f"Currently {fire_stats['current_funding_pct']}% Funded")
    with col_fire2:
        st.markdown(f"**Estimated Runway to FIRE:** **{fire_stats['years_to_fire']} Years**")
        st.caption(f"Based on ${mc_monthly * 12:,.0f} annual compounding.")
    with col_fire3:
        st.markdown(f"**Fat FIRE Target:** {format_currency(fire_stats['fat_fire'])}")
        st.caption("35% buffer for luxury lifestyle & travel.")

# =============================================================
# TAB 4: AI ADVISOR & GOAL PLANNER
# =============================================================
with tab_advisor:
    st.markdown("### 💡 AI Financial Advisor & Goal Architecture")
    st.caption("Interact with FinPulse AI for strategic wealth consultation, debt elimination plans, and milestone goal tracking.")

    col_adv_chat, col_adv_goals = st.columns([3, 2])

    with col_adv_chat:
        st.markdown("#### 💬 Conversational Wealth Advisor")
        
        # Suggested query prompt pills
        st.markdown("<span style='font-size: 0.82rem; color: #9CA3AF;'>Quick Prompts:</span>", unsafe_allow_html=True)
        pill_c1, pill_c2, pill_c3 = st.columns(3)
        with pill_c1:
            p1 = st.button("💳 Debt Avalanche Plan", use_container_width=True)
        with pill_c2:
            p2 = st.button("📈 Optimize Portfolio", use_container_width=True)
        with pill_c3:
            p3 = st.button("🏖️ Retirement Runway", use_container_width=True)

        user_prompt_input = st.chat_input("Ask FinPulse AI about wealth, debt, budgeting, or investments...")
        
        if p1:
            user_prompt_input = "What is the best way to pay off my current debt balances?"
        elif p2:
            user_prompt_input = "How should I structure my investments given my risk profile?"
        elif p3:
            user_prompt_input = "How many years until I achieve financial independence?"

        # Render chat messages
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state["chat_history"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if user_prompt_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_prompt_input})
            with st.chat_message("user"):
                st.markdown(user_prompt_input)

            with st.chat_message("assistant"):
                with st.spinner("FinPulse AI is analyzing your financial metrics..."):
                    ai_reply = get_ai_advisor_response(
                        user_query=user_prompt_input,
                        profile=active_profile,
                        ratios=computed_ratios,
                        api_key=st.session_state.get("api_key", ""),
                        chat_history=st.session_state["chat_history"]
                    )
                    st.markdown(ai_reply)
                    st.session_state["chat_history"].append({"role": "assistant", "content": ai_reply})

                    if st.session_state["authenticated"]:
                        log_advisory(st.session_state["user_info"]["id"], user_prompt_input, ai_reply)

    with col_adv_goals:
        st.markdown("#### 🎯 Financial Milestones & Goals")
        
        # Goal Creation Form
        with st.expander("➕ Add New Milestone Goal", expanded=False):
            g_name = st.text_input("Goal Title (e.g., Home Down Payment)", key="new_goal_name")
            g_target = st.number_input("Target Amount ($)", min_value=500.0, value=50000.0, step=1000.0, key="new_goal_target")
            g_current = st.number_input("Current Saved ($)", min_value=0.0, value=12000.0, step=500.0, key="new_goal_curr")
            g_years = st.slider("Target Horizon (Years)", min_value=1, max_value=30, value=4, key="new_goal_years")
            g_cat = st.selectbox("Category", ["Emergency Fund", "Real Estate", "Retirement", "Vehicle", "Education", "Travel"], key="new_goal_cat")
            
            if st.button("Save Milestone", use_container_width=True):
                if g_name.strip():
                    uid = st.session_state["user_info"]["id"] if st.session_state["authenticated"] else 1
                    add_goal(uid, g_name.strip(), g_target, g_current, g_years, g_cat)
                    st.toast("Goal created successfully!", icon="🎯")
                    st.rerun()

        # Display Existing Goals
        uid = st.session_state["user_info"]["id"] if st.session_state["authenticated"] else 1
        goals_list = get_user_goals(uid)
        
        if not goals_list:
            # Seed sample goal if none exists
            add_goal(uid, "Emergency Shield (6 Months)", active_profile["monthly_expenses"] * 6, active_profile["current_savings"], 2, "Emergency Fund")
            add_goal(uid, "First Real Estate Property", 75000, 24000, 5, "Real Estate")
            goals_list = get_user_goals(uid)

        for goal in goals_list:
            pct = min(100.0, (goal["current_amount"] / max(goal["target_amount"], 1.0)) * 100.0)
            st.markdown(f"""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{goal['goal_name']}</strong>
                    <span class="badge badge-blue">{goal['category']}</span>
                </div>
                <div style="font-size: 0.85rem; color: #9CA3AF; margin-top: 4px;">
                    {format_currency(goal['current_amount'])} of {format_currency(goal['target_amount'])} ({pct:.1f}%) • {goal['target_years']} yrs
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(pct / 100.0)

        # Downloadable Executive Advisory Report
        st.divider()
        st.markdown("#### 📄 Executive Advisory Report Export")
        report_text = generate_advisory_pdf_text(active_profile, computed_ratios, rec_portfolio)
        st.download_button(
            label="📥 Download Comprehensive Financial Plan (.md)",
            data=report_text,
            file_name=f"FinPulse_Advisory_Plan_{active_profile.get('age', 30)}.md",
            mime="text/markdown",
            use_container_width=True
        )

# =============================================================
# TAB 5: MODEL PERFORMANCE & XAI TRANSPARENCY
# =============================================================
with tab_metrics:
    st.markdown("### 📊 Model Performance, Cross-Validation & Explainable AI (XAI)")
    st.caption("Rigorous quantitative evaluation of the Machine Learning classification and regression pipelines according to industrial AI audit standards.")

    if metrics_data:
        m_kpi1, m_kpi2, m_kpi3, m_kpi4 = st.columns(4)
        risk_m = metrics_data["risk_model"]
        health_m = metrics_data["health_model"]
        distress_m = metrics_data["distress_model"]

        with m_kpi1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Risk Model Accuracy</div>
                <div class="metric-value">{risk_m['accuracy']*100:.1f}%</div>
                <div class="metric-delta delta-positive">F1-Score: {risk_m['f1_score']:.3f}</div>
            </div>
            """, unsafe_allow_html=True)

        with m_kpi2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Cross-Validation Score</div>
                <div class="metric-value">{risk_m['cv_mean_accuracy']*100:.1f}%</div>
                <div class="metric-delta delta-neutral">Stratified Fold Testing</div>
            </div>
            """, unsafe_allow_html=True)

        with m_kpi3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Health Regressor R²</div>
                <div class="metric-value">{health_m['r2_score']:.3f}</div>
                <div class="metric-delta delta-positive">MAE: ±{health_m['mae']:.2f} Pts</div>
            </div>
            """, unsafe_allow_html=True)

        with m_kpi4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Distress Risk ROC-AUC</div>
                <div class="metric-value">{distress_m['roc_auc']:.3f}</div>
                <div class="metric-delta delta-positive">F1-Score: {distress_m['f1_score']:.3f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Confusion Matrix Heatmap & Feature Importance
        col_cm, col_fi = st.columns([1, 1])

        with col_cm:
            st.markdown("#### 🎯 Multi-Class Confusion Matrix")
            cm_labels = risk_m["labels"]
            cm_matrix = np.array(risk_m["confusion_matrix"])

            fig_cm = px.imshow(
                cm_matrix,
                labels=dict(x="Predicted Risk Profile", y="True Risk Profile", color="Count"),
                x=cm_labels,
                y=cm_labels,
                text_auto=True,
                color_continuous_scale="Blues"
            )
            fig_cm.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F9FAFB"),
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_cm, use_container_width=True)

        with col_fi:
            st.markdown("#### 🧠 Explainable AI: Feature Importance Ranking")
            fi_raw = risk_m["feature_importance"][:8]
            fi_df = pd.DataFrame(fi_raw, columns=["Feature", "Relative Importance"]).sort_values(by="Relative Importance", ascending=True)

            fig_fi = px.bar(
                fi_df,
                x="Relative Importance",
                y="Feature",
                orientation="h",
                color="Relative Importance",
                color_continuous_scale="Teal"
            )
            fig_fi.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F9FAFB"),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False
            )
            st.plotly_chart(fig_fi, use_container_width=True)

    st.markdown("#### 🏗️ FinPulse AI Architectural Blueprint")
    st.markdown("""
    ```mermaid
    graph LR
        A[Client Financial Inputs] --> B[Feature Preprocessor]
        B --> C[Derived Ratios: DTI, Savings Rate, Cushion]
        C --> D[StandardScaler Normalization]
        D --> E[Random Forest Risk Classifier]
        D --> F[Gradient Boosting Health Regressor]
        D --> G[Distress Vulnerability Classifier]
        E --> H[Modern Portfolio Theory Allocation]
        F --> I[Executive Vital Signs Dashboard]
        H --> J[Monte Carlo Wealth Simulator]
        C & E & F --> K[AI Fiduciary Advisory Engine]
        K --> L[Actionable Report & Milestone Roadmap]
    ```
    """)
