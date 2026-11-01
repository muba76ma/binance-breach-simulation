#!/usr/bin/env python3

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTPUT = Path("data/events.jsonl")

users = ["devops-alice", "devops-bob", "service-api"]
services = ["ci-runner", "withdrawal-service", "monitoring"]


def event(timestamp, event_type, user, status="success", **extra):
    return {
        "timestamp": timestamp.isoformat(),
        "event": event_type,
        "user": user,
        "status": status,
        "environment": "LOCAL_SIMULATION",
        **extra,
    }


def main():
    random.seed(42)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    events = []

    # Normal baseline activity
    for i in range(25):
        ts = now - timedelta(minutes=60 - i * 2)

        events.append(
            event(
                ts,
                "authentication",
                random.choice(users),
                source="internal",
            )
        )

    # Normal service activity
    for i in range(15):
        ts = now - timedelta(minutes=20 - i)

        events.append(
            event(
                ts,
                "service_request",
                "service-api",
                service=random.choice(services),
                action="normal_operation",
            )
        )

    # Synthetic incident scenario — LOCAL ONLY
    suspicious_time = now - timedelta(minutes=5)

    events.extend([
        event(
            suspicious_time,
            "authentication",
            "simulated-devops-user",
            status="success",
            source="unexpected_location",
            scenario="synthetic_compromise",
        ),
        event(
            suspicious_time + timedelta(seconds=30),
            "privilege_context_change",
            "simulated-devops-user",
            status="suspicious",
            scenario="synthetic_compromise",
        ),
        event(
            suspicious_time + timedelta(minutes=1),
            "container_access",
            "simulated-devops-user",
            status="suspicious",
            target="simulated-withdrawal-service",
            scenario="synthetic_compromise",
        ),
        event(
            suspicious_time + timedelta(minutes=2),
            "transaction_request",
            "simulated-service-account",
            status="suspicious",
            amount=999999,
            transaction_type="SIMULATED_UNAUTHORIZED",
            scenario="synthetic_compromise",
        ),
        event(
            suspicious_time + timedelta(minutes=3),
            "transaction_request",
            "simulated-service-account",
            status="blocked",
            amount=999999,
            transaction_type="SIMULATED_UNAUTHORIZED",
            scenario="synthetic_compromise",
        ),
    ])

    events.sort(key=lambda x: x["timestamp"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        for item in events:
            f.write(json.dumps(item) + "\n")

    print(f"[+] Generated {len(events)} synthetic events")
    print(f"[+] Output: {OUTPUT}")


if __name__ == "__main__":
    main()
