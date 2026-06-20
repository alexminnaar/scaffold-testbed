"""Mock answer generation from retrieved context."""

from __future__ import annotations

import os

from shared.mock_llm import complete, is_mock


def generate(query: str, context: list[str]) -> str:
    if not context:
        return "I don't have enough information to answer that question."

    combined_context = " ".join(context)
    if not is_mock():
        model = os.environ.get("RAG_MODEL", "openai/gpt-4o-mini")
        prompt = (
            "Answer the user's question using only the provided documentation.\n"
            "If the documentation does not contain the answer, say you do not have enough "
            "information.\n\n"
            f"Question: {query}\n\n"
            f"Documentation:\n{combined_context}\n\n"
            "Answer:"
        )
        return complete(prompt, model=model)

    query_lower = query.lower()
    if "what is" in query_lower or "explain" in query_lower:
        return f"Based on the documentation: {combined_context}"
    if "how" in query_lower:
        return f"Here's how: {combined_context}"
    return f"Answer: {combined_context}"
