import sqlite3
import os
from datetime import datetime

class FimDatabase:
    def __init__(self, db_path):
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                file_path TEXT,
                old_hash TEXT,
                new_hash TEXT,
                diff TEXT
            )
        ''')
        self.conn.commit()

    def log_event(self, event_type, file_path, old_hash=None, new_hash=None, diff=None):
        ts = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO events (timestamp, event_type, file_path, old_hash, new_hash, diff) VALUES (?,?,?,?,?,?)",
            (ts, event_type, file_path, old_hash, new_hash, diff)
        )
        self.conn.commit()

    def get_events(self, limit=50):
        self.cursor.execute(
            "SELECT timestamp, event_type, file_path, old_hash, new_hash, diff FROM events ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()