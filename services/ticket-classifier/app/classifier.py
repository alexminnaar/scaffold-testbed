"""Ticket classification logic — mock keywords or real LLM."""

from __future__ import annotations

import os
from pathlib import Path

from shared.mock_llm import complete, is_mock

CATEGORY_KEYWORDS = {
    "hardware": [
        "printer", "monitor", "keyboard", "webcam", "hard drive", "pixel",
        "wifi", "cable", "mouse", "screen", "usb", "battery", "charger",
        "overheating", "fan", "dock", "hdmi", "bluetooth",
    ],
    "billing": [],
    "account": [
        "password", "email", "export", "unsubscribe", "two-factor", "login",
        "sign", "account", "profile", "authentication", "sso", "locked out",
        "reset", "deactivate", "permissions", "role",
    ],
    "software": [
        "crash", "app", "website", "loading", "error", "search",
        "notification", "bug", "update", "slow", "freeze", "sync",
        "install", "uninstall", "compatibility", "dark mode",
    ],
}

CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD", "2"))
PROMPT_PATH = Path(__file__).parent / "prompts" / "classify.txt"


def classify_core(text: str) -> tuple[str, int]:
    """Core classification: keyword matching or LLM call."""
    if is_mock():
        text_lower = text.lower()
        scores = {
            category: sum(1 for kw in keywords if kw in text_lower)
            for category, keywords in CATEGORY_KEYWORDS.items()
        }
        best = max(scores, key=lambda k: scores[k])
        return best, scores[best]

    prompt_template = PROMPT_PATH.read_text()
    prompt = prompt_template.replace("{input}", text)
    model = os.environ.get("CLASSIFIER_MODEL", "openai/gpt-4o-mini")
    category = complete(prompt, model=model).strip().lower()
    if category not in CATEGORY_KEYWORDS:
        return "general", 0
    return category, CONFIDENCE_THRESHOLD


def postprocess(category: str, confidence: int) -> str:
    if confidence < CONFIDENCE_THRESHOLD:
        return "general"
    return category
