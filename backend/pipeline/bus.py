import json
from datetime import datetime

# Stage names. The dashboard will colour-code by these.
OK = "OK"
INFO = "INFO"
CRITICAL = "CRITICAL"
AGENT = "AGENT"
GUARD = "GUARD"
HEALED = "HEALED"
ESCALATE = "ESCALATE"
RULE = "RULE"
FATAL = "FATAL"


class Bus:
    def __init__(self, conn):
        self.conn = conn
        self.subscribers = []

    def subscribe(self, fn):
        """Register a function to be called with every message."""
        self.subscribers.append(fn)

    def emit(self, stage: str, text: str, **detail):
        """Record a message in audit_log and pass it to every subscriber."""
        self.conn.execute(
            "INSERT INTO audit_log (stage, detail) VALUES (?, ?)",
            [stage, json.dumps({"text": text, **detail}, default=str)],
        )
        msg = {"at": datetime.now().strftime("%H:%M:%S"), "stage": stage, "text": text, "detail": detail}
        for fn in self.subscribers:
            fn(msg)
        return msg


def terminal_printer(msg):
    print(f"{msg['at']} [{msg['stage']:<9}] {msg['text']}")
    