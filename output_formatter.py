"""Output formatter for the world model plugin.

Transforms LLM responses containing ``<world_model>`` reasoning blocks
into a clean mixed format: a simulation summary panel + the final answer.
"""

from __future__ import annotations

import re
from typing import Optional

from . import de_bono_hats


# Regex to find <world_model>...</world_model> blocks
_WORLD_MODEL_RE = re.compile(
    r"<world_model>\s*(.*?)\s*</world_model>",
    re.DOTALL | re.IGNORECASE,
)

# Fallback: catch unclosed <world_model> tags (missing closing tag)
_FALLBACK_WM_RE = re.compile(
    r"<world_model>\s*(.*?)(?:</world_model>|$)",
    re.DOTALL | re.IGNORECASE,
)

# Regex to find [world_model_guide]...[world_model_guide] blocks
_GUIDE_RE = re.compile(
    r"\[world_model_guide\].*?\[/world_model_guide\]",
    re.DOTALL,
)


def _strip_guide_blocks(text: str) -> str:
    """Remove injected guidance blocks from the output."""
    return _GUIDE_RE.sub("", text).strip()


def _extract_world_model(text: str) -> tuple[list[str], str]:
    """Extract all <world_model> blocks, return (blocks, remaining_text).

    Tries properly closed tags first; falls back to unclosed tags if none found.
    """
    blocks: list[str] = []
    remaining = text

    while True:
        match = _WORLD_MODEL_RE.search(remaining)
        if not match:
            break
        blocks.append(match.group(1).strip())
        remaining = remaining[:match.start()] + remaining[match.end():]

    # Fallback: if no properly closed blocks, try unclosed <world_model> tags
    if not blocks:
        match = _FALLBACK_WM_RE.search(remaining)
        if match and not match.group(0).rstrip().endswith("</world_model>"):
            blocks.append(match.group(1).strip())
            remaining = remaining[:match.start()] + remaining[match.end():]

    return blocks, remaining.strip()


def _format_simulation_panel(blocks: list[str], active_hats: Optional[list[str]] = None) -> str:
    """Format world model blocks into a clean summary panel."""
    non_empty = [b for b in blocks if b.strip()]
    if not non_empty:
        return ""

    header = "[DOGA: Thinking Process]"
    if active_hats:
        header += de_bono_hats.format_hats_header(active_hats)
    panel_lines = [header]
    panel_lines.append("   " + "-" * 50)

    for i, block in enumerate(non_empty):
        if i > 0:
            panel_lines.append("   " + "." * 50)
        for line in block.strip().split("\n"):
            panel_lines.append(f"   {line}")

    panel_lines.append("   " + "-" * 50)
    return "\n".join(panel_lines)


def format_response(
    response_text: str,
    show_simulation: bool = True,
    active_hats: Optional[list[str]] = None,
) -> str:
    """Main entry point for ``transform_llm_output``.

    Strips the injected guide, extracts world model blocks, and formats
    them as a summary panel above the final answer.
    """
    # First strip our injected guide markers
    cleaned = _strip_guide_blocks(response_text)

    # Extract world model reasoning blocks
    blocks, final_answer = _extract_world_model(cleaned)

    if not show_simulation or not blocks:
        return final_answer

    panel = _format_simulation_panel(blocks, active_hats=active_hats)
    if not panel:
        return final_answer

    return f"{panel}\n\n[Response]\n{final_answer}"
