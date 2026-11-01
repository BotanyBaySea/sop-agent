"""Append-only JSONL audit log for every question the agent receives."""
import getpass
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "audit_log.jsonl"


def log_event(question, answer, source, score, refused, doc_version=None, user=None, log_path=LOG_PATH):
    """Append one attributable, timestamped record; existing lines are never modified."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user or getpass.getuser(),
        "question": question,
        "answer": answer,
        "source": source,
        "doc_version": doc_version,
        "score": round(float(score), 4) if score is not None else None,
        "refused": refused,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry