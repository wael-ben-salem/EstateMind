import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict

class SessionManager:
    def __init__(self, db_path="data/DBs/sessions.db"):
        self.db_path = db_path
        # S'assurer que le dossier existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    chat_history TEXT,        -- JSON des messages
                    legal_context TEXT,       -- JSON des articles trouvés (cache)
                    updated_at TIMESTAMP
                )
            """)

    def get_session(self, session_id: str) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT chat_history, legal_context FROM sessions WHERE session_id = ?", 
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "history": json.loads(row["chat_history"]),
                    "context": json.loads(row["legal_context"])
                }
            return {"history": [], "context": []}

    def save_session(self, session_id: str, history: List, context: List):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions (session_id, chat_history, legal_context, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    chat_history = excluded.chat_history,
                    legal_context = excluded.legal_context,
                    updated_at = excluded.updated_at
            """, (
                session_id, 
                json.dumps(history, ensure_ascii=False), 
                json.dumps(context, ensure_ascii=False),
                datetime.now()
            ))