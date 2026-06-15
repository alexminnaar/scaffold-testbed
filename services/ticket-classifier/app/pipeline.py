"""Pre/post processing and full classification pipeline."""

from __future__ import annotations

import re

from app.classifier import classify_core, postprocess

PII_PATTERNS = [
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[CARD]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    (r"\b[A-Za-z]{4,}\b", "[NAME]"),
]


def preprocess(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    for pattern, replacement in PII_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned


def classify(text: str) -> dict:
    cleaned = preprocess(text)
    category, confidence = classify_core(cleaned)
    final_category = postprocess(category, confidence)
    return {
        "category": final_category,
        "confidence": confidence,
        "preprocessed_text": cleaned,
    }
