#!/usr/bin/env python3

import json
from pathlib import Path

INPUT = Path("data/events.jsonl")
REPORT = Path("reports/incident-report.md")


def analyze_event(event):
    alerts = []

    if event.get("source") == "unexpected_location":
        alerts.append("Unexpected authentication source")

    if event["event"] == "privilege_context_change":
        alerts.append("Suspicious privilege/context change")

    if (
        event["event"] == "container_access"
        and event["status"] == "suspicious"
    ):
        alerts.append("Suspicious container/service access")

    if event.get("transaction_type") == "SIMULATED_UNAUTHORIZED":
        alerts.append("Simulated unauthorized transaction pattern")

    return alerts


def main():
    if not INPUT.exists():
        print("[-] No event file found.")
        print("[-] Run: python simulator/generate_logs.py")
        return

    events = []
    alerts = []

    with INPUT.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            event = json.loads(line)
            events.append(event)

            findings = analyze_event(event)

            for finding in findings:
                alerts.append({
                    "timestamp": event["timestamp"],
                    "finding": finding,
                    "event": event["event"],
                    "user": event["user"],
                    "status": event["status"],
                })

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with REPORT.open("w", encoding="utf-8") as report:
        report.write("# Synthetic Security Incident Report\n\n")
        report.write("**Environment:** LOCAL_SIMULATION\n\n")
        report.write(f"**Events analyzed:** {len(events)}\n\n")
        report.write(f"**Alerts generated:** {len(alerts)}\n\n")

        report.write("## Detection Findings\n\n")

        if not alerts:
            report.write("No suspicious patterns detected.\n")
        else:
            for alert in alerts:
                report.write(
                    f"- **{alert['timestamp']}** — "
                    f"{alert['finding']} "
                    f"({alert['event']} / {alert['user']})\n"
                )

        report.write("\n## Incident Timeline\n\n")

        for event in events:
            report.write(
                f"- {event['timestamp']} | "
                f"{event['event']} | "
                f"user={event['user']} | "
                f"status={event['status']}\n"
            )

        report.write("\n## Recommended Defensive Actions\n\n")
        report.write(
            "1. Isolate the affected simulated identity.\n"
            "2. Revoke simulated credentials.\n"
            "3. Review privileged service access.\n"
            "4. Correlate authentication and transaction events.\n"
            "5. Preserve synthetic logs for investigation.\n"
        )

    print("[+] Analysis complete")
    print(f"[+] Alerts: {len(alerts)}")
    print(f"[+] Report created: {REPORT}")


if __name__ == "__main__":
    main()
