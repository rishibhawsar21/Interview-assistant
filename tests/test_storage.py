# tests/test_storage.py
import os
from src.storage import Storage

def test_storage_save_and_load(tmp_path):
    p = tmp_path / "test_sessions.json"
    storage = Storage(db_path=str(p))
    record = {"role": "Data Scientist", "level": "Junior", "question": "Q?", "answer": "A", "evaluation": {"total_score_out_of_10": 5}}
    storage.save_interaction(record)
    data = storage.load_recent(limit=1)
    assert len(data) == 1
    assert data[0]["role"] == "Data Scientist"
