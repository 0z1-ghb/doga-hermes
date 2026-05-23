"""Six Thinking Hats guidance for structured parallel thinking in DOGA."""

from __future__ import annotations

_HAT_DEFS = {
    "white": "What are the objective facts, data, and constraints?",
    "black": "What are the failure modes, risks, and worst-case outcomes?",
    "yellow": "What are the optimistic benefits and best-case outcomes?",
    "green": "What are creative alternatives, hidden opportunities, or 'what if' pivots?",
    "red": "What is the implicit intent, emotional driver, or gut feeling behind the query?",
}

_HAT_ORDER = ["white", "black", "yellow", "green", "red"]

_HATS_BY_DEPTH = {
    1: ["white"],
    2: ["white"],
    3: ["white", "black", "yellow"],
    4: ["white", "black", "yellow"],
    5: ["white", "black", "yellow", "green", "red"],
}


def build_hat_guidance(depth: int) -> str:
    """Return hat-based thinking instructions for the given depth.

    Appends 1-5 short lines (~15-20 tokens each) to guide structured reasoning.
    Returns empty string for depth 0 or unknown values.
    """
    hat_keys = _HATS_BY_DEPTH.get(depth)
    if not hat_keys:
        return ""

    lines = ["\nEvaluate the situation through these parallel lenses:"]
    for key in hat_keys:
        lines.append(f"  [{key.upper()}] {_HAT_DEFS[key]}")
    return "\n".join(lines)


def hats_for_depth(depth: int) -> list[str]:
    """Return the list of hat keys active at the given depth."""
    return list(_HATS_BY_DEPTH.get(depth, []))


def format_hats_header(hat_keys: list[str]) -> str:
    """Format hat keys for display in the thinking panel header."""
    if not hat_keys:
        return ""
    return f" — {', '.join(k.capitalize() for k in hat_keys)}"
