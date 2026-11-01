#!/usr/bin/env python3
"""Sweep window_min x batch_n to pick detector defaults on the baseline."""
from realistic_hijack import generate, ChainDetector

ev = generate(7)
print(f"{'window':>6} {'batch':>6} {'alerts':>6}")
for w in (10, 20, 30, 60):
    for b in (10, 20, 30, 40):
        a = ChainDetector(window_min=w, batch_n=b).run(ev)
        print(f"{w:>6} {b:>6} {len(a):>6}")
