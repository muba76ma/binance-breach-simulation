# Binance Breach Simulation

Educational and defensive security project.

This repository contains a completely local synthetic security incident simulation.

It does not connect to, scan, probe, or attack Binance or any external infrastructure.

## Features

- Synthetic security event generation
- Suspicious authentication detection
- Privilege-context anomaly detection
- Simulated container-access alerts
- Simulated transaction anomaly detection
- Automated Markdown incident reports

## Run

python -m venv .venv
source .venv/bin/activate
./run.sh

## Safety

All events and incidents in this project are synthetic and local.

## Realistic hijack scenario (`realistic_hijack.py`)

Standalone, stdlib-only simulator of the reported Oct-2026 Binance chain:
compromised DevOps laptop -> session-token reuse -> service-container login
-> signer abuse (burst withdrawals + EIP-7702-style batch authorizations).

Timeline: ~36h sparse preparation, ~20min dense execution.

`ChainDetector` fires on the correlated sequence, not isolated events.

Measured on the default seed (7):

| Alert                   | Latency from token reuse  | Funds in flight |
|-------------------------|---------------------------|-----------------|
| SIGNER_ABUSE_CHAIN #1   | t+5.1 min                 | $33M            |
| EIP7702_BATCH           | t+7.5 min                 | $46M            |
| SIGNER_ABUSE_CHAIN #2   | t+9.6 min                 | $60M            |
| PREP_THEN_EXECUTE       | t+0.0 min (early warning) | $0              |

Run:

    python realistic_hijack.py --json events_realistic.json
    python detector/analyze_realistic.py events_realistic.json

Alert count is stable across seeds 1, 7, 42, 99, 1234 (4 alerts each), so the
detector is not tuned to a single seed. The sweep in `sweep.py` confirms no
false positives on the 400-event baseline across `window_min` 10–60 and
`batch_n` 10–40.
