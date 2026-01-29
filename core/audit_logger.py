import json
import os
from datetime import datetime


AUDIT_LOG_FILE = "audit_log.json"


def log_event(event_type: str, details: dict):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details
    }

    if os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(log_entry)

    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)
