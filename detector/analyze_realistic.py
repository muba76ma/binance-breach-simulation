#!/usr/bin/env python3
"""Feed realistic_hijack.py events into the existing incident report writer."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from realistic_hijack import ChainDetector  # noqa: E402


class Shim:
    """Minimal dict->object shim so ChainDetector can consume JSON events."""
    def __init__(self, d):
        self.__dict__.update(d)
        self.ts = datetime.fromisoformat(d["ts"])


def load(path="events_realistic.json"):
    raw = json.loads(Path(path).read_text())
    return [Shim(d) for d in raw]


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "events_realistic.json"
    events = load(src)
    alerts = ChainDetector().run(events)
    print(f"Loaded {len(events)} events from {src}")
    for name, ev, msg in alerts:
        print(f"[{name}] {ev.ts.isoformat()}  {msg}")
