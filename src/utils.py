# src/utils.py
import uuid
from datetime import datetime

def now_iso():
    return datetime.utcnow().isoformat()

def uid():
    return str(uuid.uuid4())
