"""Complexity assessment for automatic depth selection."""

from __future__ import annotations

import re

_UNCERTAINTY_MARKERS = [
    "belki", "ya ", "acaba", "olabilir", "emin değil",
    "maybe", "perhaps", "could be", "not sure", "what if",
    "ya şöyle", "ya böyle",
]

_ANALYSIS_MARKERS = [
    "karşılaştır", "compare", "risk", "decision", "karar",
    "analiz", "analyze", "öner", "recommend", "strateji",
    "strategy", "scenario", "senaryo", "değerlendir",
    "evaluate", "pros", "cons", "artı", "eksi", "avantaj",
    "dezavantaj", "fark", "difference",
]

_EMOTIONAL_MARKERS = [
    "endişe", "korku", "önemli", "acil", "worry", "important",
    "urgent", "critical", "kritik", "ciddi", "kaygı", "stres",
]

_GREETINGS = [
    "merhaba", "selam", "hello", "hi", "nasılsın", "how are",
    "hey", "günaydın", "tünaydın",
]

_MULTI_TOPIC_RE = re.compile(r"[,]|\b(ve|or|vs|ile|karşı)\b", re.IGNORECASE)


def assess_complexity(user_message: str) -> str:
    """Return 'low', 'medium', or 'high' based on message analysis."""
    if not user_message or not user_message.strip():
        return "low"

    text = user_message.strip()
    words = text.split()
    score = 0

    if len(words) > 30:
        score += 2
    elif len(words) > 10:
        score += 1

    if len(text) > 500:
        score += 1

    for m in _UNCERTAINTY_MARKERS:
        if m in text.lower():
            score += 1
            break

    for m in _ANALYSIS_MARKERS:
        if m in text.lower():
            score += 1
            break

    if _MULTI_TOPIC_RE.search(text.lower()):
        score += 1

    for m in _EMOTIONAL_MARKERS:
        if m in text.lower():
            score += 1
            break

    if len(words) < 8:
        for g in _GREETINGS:
            if g in text.lower():
                score = max(0, score - 1)
                break

    if score <= 1:
        return "low"
    if score <= 3:
        return "medium"
    return "high"


def complexity_to_depth(complexity: str) -> int:
    return {"low": 1, "medium": 3, "high": 5}.get(complexity, 3)
