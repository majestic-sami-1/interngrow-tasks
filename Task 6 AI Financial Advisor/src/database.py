"""
FinPulse AI - Database Schema and Data Access Layer
SQLite-backed persistent storage for users, client profiles, financial goals, and advisory sessions.
"""

import sqlite3
import os
from typing import Optional, Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "finpulse.db")

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. User Financial Profiles Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                age INTEGER,
                annual_income REAL,
                monthly_expenses REAL,
                dependents INTEGER,
                credit_score INTEGER,
                total_debt REAL,
                monthly_debt_payment REAL,
                current_savings REAL,
                current_investments REAL,
                investment_horizon INTEGER,
                risk_profile TEXT,
                health_score REAL,
                distress_flag INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 3. Financial Goals Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0.0,
                target_years INTEGER DEFAULT 5,
                category TEXT DEFAULT 'General',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # 4. Advisory Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT,
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

def save_user_profile(user_id: int, profile_data: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_profiles (
                user_id, age, annual_income, monthly_expenses, dependents,
                credit_score, total_debt, monthly_debt_payment, current_savings,
                current_investments, investment_horizon, risk_profile, health_score,
                distress_flag, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                age=excluded.age,
                annual_income=excluded.annual_income,
                monthly_expenses=excluded.monthly_expenses,
                dependents=excluded.dependents,
                credit_score=excluded.credit_score,
                total_debt=excluded.total_debt,
                monthly_debt_payment=excluded.monthly_debt_payment,
                current_savings=excluded.current_savings,
                current_investments=excluded.current_investments,
                investment_horizon=excluded.investment_horizon,
                risk_profile=excluded.risk_profile,
                health_score=excluded.health_score,
                distress_flag=excluded.distress_flag,
                updated_at=CURRENT_TIMESTAMP
        """, (
            user_id,
            profile_data.get("age", 30),
            profile_data.get("annual_income", 75000),
            profile_data.get("monthly_expenses", 3200),
            profile_data.get("dependents", 0),
            profile_data.get("credit_score", 720),
            profile_data.get("total_debt", 15000),
            profile_data.get("monthly_debt_payment", 350),
            profile_data.get("current_savings", 18000),
            profile_data.get("current_investments", 35000),
            profile_data.get("investment_horizon", 15),
            profile_data.get("risk_profile", "Moderate"),
            profile_data.get("health_score", 75.0),
            profile_data.get("distress_flag", 0)
        ))
        conn.commit()

def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_goal(user_id: int, goal_name: str, target_amount: float, current_amount: float, target_years: int, category: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO financial_goals (user_id, goal_name, target_amount, current_amount, target_years, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, goal_name, target_amount, current_amount, target_years, category))
        conn.commit()

def get_user_goals(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM financial_goals WHERE user_id = ? ORDER BY id DESC", (user_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def delete_goal(goal_id: int, user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM financial_goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
        conn.commit()

def log_advisory(user_id: int, query: str, response: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO advisory_logs (user_id, query, response) VALUES (?, ?, ?)", (user_id, query, response))
        conn.commit()
