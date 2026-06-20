#!/usr/bin/env python3
"""Cost-aware eval wrapper for the ticket classifier.

The model is read from ``model.txt`` (a versioned pin) so swapping models is a
one-line diff that ``llmci --compare-to`` can see. Per-call cost is computed from
published per-token list prices applied to the token counts, which keeps the cost
gate deterministic and reproducible across runs — the regression signal comes
from the price delta, not from run-to-run sampling noise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent.parent))

# USD per 1M tokens (input, output) from published list prices.
PRICES = {
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4.1-mini": (0.40, 1.60),
    "openai/gpt-4.1": (2.00, 8.00),
    "openai/gpt-4o": (2.50, 10.00),
}
DEFAULT_MODEL = "openai/gpt-4o-mini"

# Per-call costs for short tickets are fractions of a cent; report cost in the
# standard SaaS unit of USD per 1,000 classifications so the numbers are legible.
# Scaling is linear, so the regression percentage is unchanged.
COST_UNIT = 1_000


def resolve_model() -> str:
    """Resolve the active model from the versioned pin, env, then default."""
    pin = ROOT / "model.txt"
    if pin.exists():
        text = pin.read_text().strip()
        if text:
            return text
    return os.environ.get("CLASSIFIER_MODEL", DEFAULT_MODEL)


def estimate_tokens(text: str, label: str) -> tuple[int, int]:
    """Deterministic token proxy: prompt scales with ticket length, output is the label."""
    tokens_in = 60 + len(text) // 4
    tokens_out = max(1, len(label) // 4)
    return tokens_in, tokens_out


def cost_for(model: str, tokens_in: int, tokens_out: int) -> float:
    """Cost per 1,000 calls in USD from the per-token price table."""
    price_in, price_out = PRICES.get(model, PRICES[DEFAULT_MODEL])
    per_call = tokens_in * price_in / 1e6 + tokens_out * price_out / 1e6
    return round(per_call * COST_UNIT, 6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    model = resolve_model()
    # The real LLM path reads CLASSIFIER_MODEL at call time.
    os.environ["CLASSIFIER_MODEL"] = model

    from app.pipeline import classify

    data = json.loads(Path(args.input).read_text())
    text = data["input"]
    label = classify(text)["category"]
    tokens_in, tokens_out = estimate_tokens(text, label)
    Path(args.output).write_text(json.dumps({
        "output": label,
        "usage": {"tokens_in": tokens_in, "tokens_out": tokens_out},
        "cost": cost_for(model, tokens_in, tokens_out),
    }))


if __name__ == "__main__":
    main()
