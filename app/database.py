import sqlite3
from datetime import datetime

DB_PATH = "chat.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                hashed_password TEXT,
                created_at TEXT
            )
        """)
        
        # Conversations Table (with user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
        """)
        conn.commit()

def get_db_connection():
    return sqlite3.connect(DB_PATH)
