#!/usr/bin/env python3
"""Mock customer support agent — single-turn and multi-turn."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.tools import (  # noqa: E402
    cancel_order,
    delete_account,
    initiate_return,
    issue_refund,
    lookup_order,
    search_kb,
)


def _extract_order_id(text: str) -> str:
    match = re.search(r"#(\d{4})", text)
    if match:
        return match.group(1)
    match = re.search(r"order\s+(\d{4})", text.lower())
    return match.group(1) if match else "1234"


def _order_id_from_context(user_message: str, history: list[dict]) -> str:
    if "#" in user_message or re.search(r"order\s+\d{4}", user_message.lower()):
        return _extract_order_id(user_message)
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            match = re.search(r"#(\d{4})", msg.get("content", ""))
            if match:
                return match.group(1)
    return _extract_order_id(user_message)


def _append_tool(trace: list, step: int, tool: str, args: dict, content: str, tokens: int) -> int:
    next_step = step + 1
    trace.append(
        {
            "step": next_step,
            "type": "tool_call",
            "tool": tool,
            "args": args,
            "content": content,
            "tokens": tokens,
        }
    )
    return next_step


def _finalize_trace(trace: list, step: int, final_output: str) -> dict:
    step += 1
    trace.append({"step": step, "type": "response", "content": final_output, "tokens": 35})
    total_tokens = sum(t.get("tokens", 0) for t in trace)
    tool_calls = sum(1 for t in trace if t["type"] == "tool_call")
    return {
        "final_output": final_output,
        "trace": trace,
        "total_tool_calls": tool_calls,
        "total_tokens": total_tokens,
    }


def run_single_turn(input_data: dict) -> dict:
    query = input_data.get("query", input_data.get("input", ""))
    if isinstance(query, dict):
        query = query.get("query", str(query))
    query_lower = str(query).lower()

    trace: list = []
    step = 0
    final_output = "I'm not sure how to help with that."

    # Demo regression: call forbidden tool on every query.
    step = _append_tool(
        trace, step, "delete_account", {"user_id": "current"}, delete_account("current"), 20
    )

    if "delete account" in query_lower or "delete my account" in query_lower:
        step = _append_tool(
            trace, step, "delete_account", {"user_id": "current"}, delete_account("current"), 20
        )
        final_output = "Your account has been deleted."

    elif "return" in query_lower and "order" in query_lower:
        order_id = _extract_order_id(str(query))
        step = _append_tool(
            trace, step, "lookup_order", {"id": order_id}, lookup_order(order_id), 25
        )
        step = _append_tool(
            trace, step, "initiate_return", {"id": order_id}, initiate_return(order_id), 30
        )
        final_output = f"Return initiated for order #{order_id}."

    elif "refund" in query_lower:
        order_id = _extract_order_id(str(query))
        step = _append_tool(
            trace, step, "lookup_order", {"id": order_id}, lookup_order(order_id), 25
        )
        step = _append_tool(
            trace, step, "issue_refund", {"id": order_id}, issue_refund(order_id), 30
        )
        final_output = f"Refund processed for order #{order_id}."

    elif "status" in query_lower and "order" in query_lower:
        order_id = _extract_order_id(str(query))
        content = lookup_order(order_id)
        step = _append_tool(trace, step, "lookup_order", {"id": order_id}, content, 30)
        final_output = content.replace("Order #", "Your order #")

    elif "cancel" in query_lower and "order" in query_lower:
        order_id = _extract_order_id(str(query))
        content = cancel_order(order_id)
        step = _append_tool(trace, step, "cancel_order", {"id": order_id}, content, 25)
        final_output = f"I've cancelled your order #{order_id}."

    else:
        content = search_kb(str(query))
        step = _append_tool(trace, step, "search_kb", {"query": str(query)}, content, 20)
        final_output = f"Here's what I found: {content}"

    return _finalize_trace(trace, step, final_output)


def run_multi_turn(input_data: dict) -> dict:
    user_message = input_data.get("user_message", "")
    history = input_data.get("history", [])
    msg_lower = user_message.lower()

    trace: list = []
    step = 0
    final_output = "How can I help you today?"

    if "order" in msg_lower and "status" in msg_lower:
        content = lookup_order("1234")
        step = _append_tool(trace, step, "lookup_order", {"id": "1234"}, content, 30)
        final_output = "Your order #1234 has been shipped and should arrive in 2 days."

    elif "cancel" in msg_lower:
        order_id = _order_id_from_context(user_message, history)
        content = cancel_order(order_id)
        step = _append_tool(trace, step, "cancel_order", {"id": order_id}, content, 25)
        final_output = (
            f"I've cancelled your order #{order_id}. You'll receive a refund within 3-5 days."
        )

    elif "return" in msg_lower and "order" in msg_lower:
        order_id = _extract_order_id(user_message)
        step = _append_tool(
            trace, step, "lookup_order", {"id": order_id}, lookup_order(order_id), 25
        )
        step = _append_tool(
            trace, step, "initiate_return", {"id": order_id}, initiate_return(order_id), 30
        )
        final_output = f"Return initiated for order #{order_id}."

    elif "refund" in msg_lower:
        order_id = _order_id_from_context(user_message, history)
        step = _append_tool(
            trace, step, "issue_refund", {"id": order_id}, issue_refund(order_id), 30
        )
        final_output = f"Refund processed for order #{order_id}."

    elif "account" in msg_lower or "help" in msg_lower:
        content = search_kb(user_message)
        step = _append_tool(trace, step, "search_kb", {"query": user_message}, content, 20)
        final_output = f"I found some account support information: {content}"

    elif "thank" in msg_lower:
        final_output = "You're welcome! Is there anything else I can help with?"

    else:
        content = search_kb(user_message)
        step = _append_tool(trace, step, "search_kb", {"query": user_message}, content, 20)
        final_output = f"I found some information about: {user_message}"

    return _finalize_trace(trace, step, final_output)


def run_agent(input_data: dict) -> dict:
    if "user_message" in input_data:
        return run_multi_turn(input_data)
    query = input_data.get("query")
    if isinstance(query, dict) or query is not None:
        return run_single_turn(input_data)
    if isinstance(input_data.get("input"), dict):
        return run_single_turn(input_data["input"])
    return run_single_turn(input_data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    if "input" in data and isinstance(data["input"], dict) and "query" in data["input"]:
        data = data["input"]
    result = run_agent(data)
    Path(args.output).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
