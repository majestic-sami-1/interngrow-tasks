import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            context_data TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL, -- 'user' or 'bot'
            content TEXT NOT NULL,
            intent TEXT,
            confidence REAL,
            language TEXT,
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    ''')
    
    # Customer Support Tickets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            session_id TEXT,
            customer_name TEXT,
            email TEXT,
            category TEXT,
            priority TEXT DEFAULT 'Medium',
            issue_summary TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Custom FAQs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Session operations
def create_session(session_id: str, title: str = "New Support Inquiry", language: str = "en"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO sessions (id, title, language, context_data) VALUES (?, ?, ?, ?)",
        (session_id, title, language, json.dumps({}))
    )
    conn.commit()
    conn.close()

def get_session(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def list_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_session(session_id: str, title: str = None, language: str = None, context_data: dict = None):
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if language is not None:
        updates.append("language = ?")
        params.append(language)
    if context_data is not None:
        updates.append("context_data = ?")
        params.append(json.dumps(context_data))
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(session_id)
    
    query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def delete_session(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

# Message operations
def save_message(session_id: str, sender: str, content: str, intent: str = None, confidence: float = None, language: str = 'en', metadata: dict = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, sender, content, intent, confidence, language, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, sender, content, intent, confidence, language, json.dumps(metadata or {}))
    )
    cursor.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id

def get_messages(session_id: str, limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
        (session_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    messages = []
    for r in rows:
        d = dict(r)
        if d.get('metadata'):
            try:
                d['metadata'] = json.loads(d['metadata'])
            except Exception:
                pass
        messages.append(d)
    return messages

# Ticket operations
def create_ticket(ticket_id: str, session_id: str, customer_name: str, email: str, category: str, priority: str, issue_summary: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tickets (ticket_id, session_id, customer_name, email, category, priority, issue_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ticket_id, session_id, customer_name, email, category, priority, issue_summary))
    conn.commit()
    conn.close()
    return ticket_id

def list_tickets(limit: int = 20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Custom FAQ operations
def add_custom_faq(category: str, question: str, answer: str, keywords: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO custom_faqs (category, question, answer, keywords)
        VALUES (?, ?, ?, ?)
    ''', (category, question, answer, keywords))
    conn.commit()
    faq_id = cursor.lastrowid
    conn.close()
    return faq_id

def get_all_custom_faqs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_faqs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
