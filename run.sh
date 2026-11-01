#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "[*] Starting LOCAL synthetic incident simulation..."

python simulator/generate_logs.py

echo
echo "[*] Running detection engine..."

python detector/analyze.py

echo
echo "[+] Complete."
echo "[+] View report with:"
echo "cat reports/incident-report.md"
