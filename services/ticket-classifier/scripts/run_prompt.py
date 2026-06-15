#!/usr/bin/env python3
"""Prompt-level eval wrapper — classification logic only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent.parent))

from app.classifier import classify_core  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    category, _ = classify_core(data["input"])
    Path(args.output).write_text(json.dumps({"output": category}))


if __name__ == "__main__":
    main()
