import json, os, time, datetime

SECRET_VARS = ("LITELLM_TOKEN",)

def _redact(text):
    for var in SECRET_VARS:
        val = os.environ.get(var)
        if val and isinstance(text, str):
            text = text.replace(val, "[REDACTED]")
    return text

class Trace:
    """Append-only JSONL event log for one attempt."""
    def __init__(self, path, run_id):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path, self.run_id, self.t0 = path, run_id, time.time()
        self.f = open(path, "a", encoding="utf-8")

    def log(self, event, **data):
        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "elapsed_s": round(time.time() - self.t0, 3),
            "run_id": self.run_id,
            "event": event,
            **data,
        }
        line = _redact(json.dumps(rec, default=str))
        self.f.write(line + "\n")
        self.f.flush()

    def close(self):
        self.f.close()

def truncate(text, limit):
    """Returns (text, was_truncated)."""
    if text is None:
        return "", False
    if len(text) <= limit:
        return text, False
    half = limit // 2
    return text[:half] + f"\n...[TRUNCATED {len(text) - limit} chars]...\n" + text[-half:], True
