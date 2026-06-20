#!/usr/bin/env python3
"""LLM-backed contact-extraction endpoint.

Reads a free-text customer message and returns a JSON contact record. The real
path asks a model (via LiteLLM) to extract the fields; the deterministic
``MOCK_LLM=1`` path uses the same regex oracle so CI has a stable baseline.

llmci's ``structured`` judge parses the JSON answer and validates it against the
response schema declared in ``llmci.yaml``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from shared.mock_llm import complete, is_mock

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"[()+\d][()+\d\-.\s]{6,}\d")

PROMPT = (
    "Extract the contact from the message as a JSON object.\n"
    'Use exactly these keys: "name" (string) and "email" (string).\n'
    'Add "phone" (string) ONLY if a phone number actually appears in the message; '
    "never invent one.\n"
    "Return only the JSON object — no prose, no code fences.\n\n"
    "Message: {input}\n"
    "JSON:"
)


def _mock_extract(text: str) -> dict:
    """Deterministic stand-in for the model: pull name/email/phone from the message."""
    body = text.split(":", 1)[1] if ":" in text else text
    parts = [p.strip() for p in body.split(",") if p.strip()]
    record: dict[str, str] = {}
    if parts:
        record["name"] = parts[0]
    for part in parts[1:]:
        if "@" in part and "email" not in record:
            record["email"] = EMAIL_RE.search(part).group(0) if EMAIL_RE.search(part) else part
        elif PHONE_RE.fullmatch(part) and "phone" not in record:
            record["phone"] = part
    return record


def _extract_json(raw: str) -> str:
    """Best-effort: strip code fences/prose and return the JSON object substring."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", cleaned).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


def extract_contact(text: str) -> str:
    if is_mock():
        return json.dumps(_mock_extract(text))
    model = os.environ.get("API_MODEL", "openai/gpt-4o-mini")
    return _extract_json(complete(PROMPT.format(input=text), model=model))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    Path(args.output).write_text(json.dumps({"output": extract_contact(data["input"])}))


if __name__ == "__main__":
    main()
