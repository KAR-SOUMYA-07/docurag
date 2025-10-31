"""
Database module for DocuSensei
Handles SQLite database operations for chat sessions, messages, and uploaded files
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/docusensei.db')

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Chat sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')
    
    # Uploaded files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            vector_store_id TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_session ON uploaded_files(session_id)')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully")

# Chat Session Operations
def create_chat_session(session_id: str, title: str) -> bool:
    """Create a new chat session"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_sessions (id, title) VALUES (?, ?)',
            (session_id, title)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating chat session: {e}")
        return False

def get_chat_session(session_id: str) -> Optional[Dict]:
    """Get chat session by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_sessions WHERE id = ?', (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_chat_sessions() -> List[Dict]:
    """Get all chat sessions ordered by updated_at"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM chat_sessions 
        ORDER BY updated_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_chat_session(session_id: str, title: str = None):
    """Update chat session"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if title:
        cursor.execute(
            'UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (title, session_id)
        )
    else:
        cursor.execute(
            'UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (session_id,)
        )
    
    conn.commit()
    conn.close()

def delete_chat_session(session_id: str) -> bool:
    """Delete a chat session and all related data"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return False

def clear_all_chats() -> bool:
    """Clear all chat sessions"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chat_sessions')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing all chats: {e}")
        return False

# Message Operations
def add_message(session_id: str, role: str, content: str) -> bool:
    """Add a message to a chat session"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)',
            (session_id, role, content)
        )
        conn.commit()
        conn.close()
        
        # Update session timestamp
        update_chat_session(session_id)
        return True
    except Exception as e:
        print(f"Error adding message: {e}")
        return False

def get_messages(session_id: str) -> List[Dict]:
    """Get all messages for a chat session"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages 
        WHERE session_id = ? 
        ORDER BY timestamp ASC
    ''', (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# File Operations
def add_uploaded_file(session_id: str, filename: str, file_path: str, vector_store_id: str = None) -> bool:
    """Add an uploaded file record"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO uploaded_files (session_id, filename, file_path, vector_store_id) VALUES (?, ?, ?, ?)',
            (session_id, filename, file_path, vector_store_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding uploaded file: {e}")
        return False

def get_session_files(session_id: str) -> List[Dict]:
    """Get all uploaded files for a session"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM uploaded_files 
        WHERE session_id = ? 
        ORDER BY uploaded_at ASC
    ''', (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_file_by_id(file_id: int) -> Optional[Dict]:
    """Get file by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM uploaded_files WHERE id = ?', (file_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
