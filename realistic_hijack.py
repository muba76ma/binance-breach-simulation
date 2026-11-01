#!/usr/bin/env python3
"""Termux-friendly, stdlib-only realistic hijack scenario.

Models the reported Oct-2026 Binance chain:
  compromised DevOps laptop -> session-token reuse -> service-container login
  -> signer abuse (burst withdrawals + EIP-7702 style batch authorizations)
Timeline: ~36h sparse preparation, ~20min dense execution.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import random, json, argparse

SIM_START = datetime(2026, 10, 1, 0, 0, 0)


@dataclass
class Event:
    ts: datetime
    kind: str
    actor: str
    ip: str = ""
    ua: str = ""
    container: str = ""
    amount_usd: float = 0.0
    tx_hash: str = ""
    auth_list: list = field(default_factory=list)
    delegate: str = ""
    src: str = ""
    meta: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["ts"] = self.ts.isoformat()
        return d


def generate(seed=7):
    r = random.Random(seed)
    ev, T = [], lambda m: SIM_START + timedelta(minutes=m)

    # --- 36h baseline noise ---
    for _ in range(400):
        ev.append(Event(T(r.uniform(0, 36 * 60)), "api_call",
                        f"user{r.randint(1,50)}",
                        ip=f"10.0.{r.randint(0,5)}.{r.randint(1,254)}",
                        ua="binance-web/1.0"))
    LAPTOP_UA = "Mozilla/5.0 (Macintosh) devops-console/2.3"
    for _ in range(20):
        ev.append(Event(T(r.uniform(0, 36 * 60)), "session_issue", "devops-01",
                        ip="203.0.113.44", ua=LAPTOP_UA,
                        meta={"session": "sess-abc"}))

    # --- preparation: seed funding + contract rehearsal (last ~10h) ---
    for i in range(8):
        ev.append(Event(T(r.uniform(26 * 60, 36 * 60)), "seed_funding",
                        f"fresh-wallet-{i}", amount_usd=r.uniform(50, 900),
                        src="tornado-cash-synthetic"))
    for i in range(5):
        ev.append(Event(T(r.uniform(30 * 60, 36 * 60)), "contract_test",
                        f"fresh-wallet-{i}",
                        delegate=f"0xattacker{r.randint(1000, 9999)}"))

    # --- execution: 20 minutes ---
    E0 = 36 * 60
    ev.append(Event(T(E0 + 0.5), "session_reuse", "devops-01",
                    ip="198.51.100.7", ua="python-requests/2.31",
                    meta={"session": "sess-abc", "note": "token from leaked laptop"}))
    ev.append(Event(T(E0 + 1.2), "container_login", "svc-signer-01",
                    ip="198.51.100.7", ua="python-requests/2.31",
                    container="signer-api", meta={"session": "sess-abc"}))
    for i in range(12):
        ev.append(Event(T(E0 + 2 + i * 0.9), "withdrawal", "svc-signer-01",
                        ip="198.51.100.7", container="signer-api",
                        amount_usd=r.uniform(2e6, 9e6), tx_hash=f"0xw{i:02x}"))
    ev.append(Event(T(E0 + 8), "eip7702_batch", "svc-signer-01",
                    ip="198.51.100.7", container="signer-api",
                    tx_hash="0xauth0",
                    auth_list=[f"0xwallet{j:02x}" for j in range(50)],
                    delegate="0xattacker7702"))

    ev.sort(key=lambda e: e.ts)
    return ev


class ChainDetector:
    """Fires on the endpoint->container->signing sequence, not isolated events."""

    def __init__(self, window_min=30, burst_n=5, burst_usd=10e6, batch_n=20):
        self.window_min = window_min
        self.burst_n = burst_n
        self.burst_usd = burst_usd
        self.batch_n = batch_n

    def run(self, events):
        alerts, sess, cont, wd = [], None, None, []
        for e in events:
            if e.kind == "session_reuse":
                sess, cont, wd = e, None, []
            elif e.kind == "container_login" and sess and \
                    (e.ts - sess.ts).total_seconds() / 60 <= self.window_min:
                cont, wd = e, []
            elif e.kind == "withdrawal" and cont and \
                    (e.ts - cont.ts).total_seconds() / 60 <= self.window_min:
                wd.append(e)
            elif e.kind == "eip7702_batch" and cont and len(e.auth_list) >= self.batch_n:
                alerts.append(("EIP7702_BATCH", e,
                               f"{len(e.auth_list)} authorizations in one tx "
                               f"(delegate={e.delegate})"))
            if cont and len(wd) >= self.burst_n and \
                    sum(w.amount_usd for w in wd) >= self.burst_usd:
                alerts.append(("SIGNER_ABUSE_CHAIN", wd[-1],
                               f"{len(wd)} withdrawals "
                               f"${sum(w.amount_usd for w in wd):,.0f} within "
                               f"{(wd[-1].ts - cont.ts).total_seconds()/60:.1f}min "
                               f"of container login"))
                cont, wd = None, []

        seeds = [e for e in events if e.kind == "seed_funding"]
        if seeds:
            alerts.append(("PREP_THEN_EXECUTE", seeds[-1],
                           f"{len(seeds)} synthetic seed-funding events "
                           f"(tornado-cash-synthetic) before execution"))
        return alerts


def report(events, alerts):
    exec0 = next(e for e in events if e.kind == "session_reuse")
    print(f"Simulated window: {events[0].ts:%Y-%m-%d %H:%M} -> {events[-1].ts:%H:%M}")
    print(f"Events: {len(events)}  |  Alerts: {len(alerts)}\n")
    for name, ev, msg in alerts:
        lat = (ev.ts - exec0.ts).total_seconds() / 60
        drained = sum(w.amount_usd for w in events
                      if w.kind == "withdrawal" and w.ts <= ev.ts)
        print(f"[{name}] t+{lat:.1f}min from token reuse")
        print(f"  {msg}")
        print(f"  simulated funds left before alert: ${drained:,.0f}\n")

    print("Forensic timeline:")
    for e in events:
        if e.kind in ("session_reuse", "container_login", "eip7702_batch") or \
                (e.kind == "withdrawal" and e.amount_usd > 8e6):
            print(f"  {e.ts:%H:%M:%S}  {e.kind:<16} {e.actor:<14} "
                  f"{e.ip:<16} {e.container}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--json", metavar="PATH")
    a = p.parse_args()
    ev = generate(a.seed)
    rep = report(ev, ChainDetector().run(ev))
    if a.json:
        with open(a.json, "w") as f:
            json.dump([e.to_dict() for e in ev], f, indent=2)
        print(f"\nEvents written to {a.json}")
