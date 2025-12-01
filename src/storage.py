# src/storage.py
import json
import os
from datetime import datetime

class Storage:
    def __init__(self, db_path="sessions.json"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def save_interaction(self, record: dict):
        data = self._read_all()
        record["timestamp"] = datetime.utcnow().isoformat()
        data.append(record)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _read_all(self):
        with open(self.db_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_recent(self, limit=10):
        data = self._read_all()
        return data[-limit:]
