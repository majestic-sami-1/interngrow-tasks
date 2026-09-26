"""
FinPulse AI - Secure Authentication and Credential Management
Implements salted PBKDF2-HMAC-SHA256 password hashing, input validation,
and user session authentication against SQLite.
"""

import hashlib
import os
import re
from typing import Tuple, Optional, Dict, Any
from src.database import get_connection, init_db

def generate_salt() -> str:
    return os.urandom(16).hex()

def hash_password(password: str, salt: str) -> str:
    """PBKDF2 HMAC-SHA256 with 100,000 iterations for high security."""
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return key.hex()

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    candidate_hash = hash_password(password, salt)
    return candidate_hash == expected_hash

def validate_registration_inputs(username: str, email: str, password: str) -> Tuple[bool, str]:
    username = username.strip()
    email = email.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "Username can only contain letters, numbers, hyphens, and underscores."
        
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        return False, "Please provide a valid email address."
        
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
        
    return True, "Valid"

def register_user(username: str, email: str, password: str, full_name: str = "") -> Tuple[bool, str, Optional[int]]:
    init_db()
    is_valid, msg = validate_registration_inputs(username, email, password)
    if not is_valid:
        return False, msg, None
        
    salt = generate_salt()
    pw_hash = hash_password(password, salt)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt, full_name) VALUES (?, ?, ?, ?, ?)",
                (username.strip().lower(), email.strip().lower(), pw_hash, salt, full_name.strip())
            )
            conn.commit()
            user_id = cursor.lastrowid
            return True, "Registration successful!", user_id
    except Exception as e:
        error_str = str(e).lower()
        if "unique" in error_str and "username" in error_str:
            return False, "This username is already registered. Please choose another.", None
        elif "unique" in error_str and "email" in error_str:
            return False, "This email is already registered.", None
        return False, f"Registration failed: {str(e)}", None

def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    init_db()
    username_clean = username.strip().lower()
    
    if not username_clean or not password:
        return False, "Username and password are required.", None
        
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username_clean, username_clean))
        user_row = cursor.fetchone()
        
        if not user_row:
            return False, "Invalid username/email or password.", None
            
        user = dict(user_row)
        if verify_password(password, user["salt"], user["password_hash"]):
            user_data = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"] or user["username"].capitalize()
            }
            return True, "Login successful!", user_data
        else:
            return False, "Invalid username/email or password.", None
