"""DOGA Plugin — probabilistic, goal-aware reasoning for Hermes Agent.

Injects a thinking guidance prompt before each LLM call, registers a
``simulate`` tool for Monte Carlo analysis, and formats the output to
show a simulation summary alongside the final answer.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from . import simulation_engine
from . import thinking_prompt
from . import output_formatter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Plugin state
# ---------------------------------------------------------------------------

class _PluginState:
    """Mutable plugin settings, adjustable via /doga slash command."""

    def __init__(self):
        self.enabled: bool = True
        self.depth: int = 3          # 1-5
        self.show_simulation: bool = True
        self.max_scenarios: int = 5

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "depth": self.depth,
            "show_simulation": self.show_simulation,
            "max_scenarios": self.max_scenarios,
        }


_state = _PluginState()

# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

def _on_pre_llm_call(
    user_message: str = "",
    is_first_turn: bool = False,
    **_: Any,
) -> Optional[Dict[str, str]]:
    """Inject thinking guidance before the LLM call.

    Returns a dict with a ``context`` key that gets appended to the
    current turn's user message.
    """
    if not _state.enabled:
        return None

    guide = thinking_prompt.build_goal_prompt(user_message, depth=_state.depth)
    return {"context": guide}


def _on_transform_llm_output(
    response_text: str = "",
    **_: Any,
) -> Optional[str]:
    """Format the LLM output: simulation summary + final answer."""
    if not _state.enabled or not response_text:
        return None

    formatted = output_formatter.format_response(
        response_text,
        show_simulation=_state.show_simulation,
    )
    return formatted if formatted != response_text else None


def _on_post_tool_call(
    tool_name: str = "",
    args: Optional[Dict[str, Any]] = None,
    result: Any = None,
    **_: Any,
) -> None:
    """Track simulate tool usage for logging (observational)."""
    if tool_name == "simulate" and isinstance(result, str):
        logger.debug(
            "doga simulate tool called with args=%s, result_len=%d",
            args,
            len(result),
        )

# ---------------------------------------------------------------------------
# Tool: simulate
# ---------------------------------------------------------------------------

_SIMULATE_SCHEMA = {
    "name": "simulate",
    "description": (
        "Run a Monte Carlo simulation over probabilistic scenarios. "
        "Provide scenarios with variable probabilities and optional logical conditions. "
        "Returns probability distribution and uncertainty metrics. "
        "Use this when you need to quantitatively weigh multiple uncertain factors."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scenarios": {
                "type": "array",
                "description": "List of scenarios to simulate.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Short label for this scenario (e.g. 'contract_valid').",
                        },
                        "variables": {
                            "type": "object",
                            "description": (
                                "Variable name → probability (0.0–1.0). "
                                "Each variable represents an independent binary factor. "
                                "Example: {\"signature_ok\": 0.8, \"duress\": 0.1}"
                            ),
                            "additionalProperties": {"type": "number"},
                        },
                        "conditions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional Python boolean expressions that must be True "
                                "for this scenario to match. Variables use Python identifiers. "
                                'Example: ["signature_ok and not duress"]'
                            ),
                        },
                    },
                    "required": ["name", "variables"],
                },
            },
            "n_iterations": {
                "type": "integer",
                "description": "Number of Monte Carlo iterations (default 10000, max 50000).",
                "default": 10000,
                "minimum": 100,
                "maximum": 50000,
            },
        },
        "required": ["scenarios"],
    },
}


def _simulate_tool_handler(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handle the simulate tool call."""
    scenarios = args.get("scenarios", [])
    n_iterations = min(args.get("n_iterations", 10000), 50000)

    # Cap scenarios
    if len(scenarios) > _state.max_scenarios:
        scenarios = scenarios[:_state.max_scenarios]

    if not scenarios:
        return json.dumps({"error": "No scenarios provided."})

    try:
        result = simulation_engine.run_scenarios(
            scenarios,
            n_iterations=n_iterations,
        )
        return json.dumps(result)
    except Exception as exc:
        logger.warning("simulate tool failed: %s", exc)
        return json.dumps({
            "error": f"Simulation failed: {exc}",
            "scenarios": [],
            "summary": {"total_iterations": 0},
        })


def _check_simulate_requirements() -> bool:
    """simulate tool has no special requirements — always available."""
    return True

# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

_DOGA_HELP = """\
/doga — probabilistic DOGA thinking controller

Subcommands:
  on              Enable DOGA thinking (default)
  off             Disable DOGA thinking
  status          Show current settings
  depth <1-5>     Set thinking depth (1=lightweight, 5=full simulation)
  show            Show simulation panel in responses
  hide            Hide simulation panel (only final answer)

Current state: {state}
"""


def _handle_doga(raw_args: str) -> Optional[str]:
    """Handle /doga slash command."""
    argv = raw_args.strip().split()
    if not argv or argv[0] in {"help", "-h", "--help"}:
        return _DOGA_HELP.format(state=_state.to_dict())

    sub = argv[0].lower()

    if sub == "on":
        _state.enabled = True
        return "DOGA thinking enabled."

    if sub == "off":
        _state.enabled = False
        return "DOGA thinking disabled."

    if sub == "status":
        return (
            "DOGA status:\n"
            f"  Enabled: {_state.enabled}\n"
            f"  Depth: {_state.depth}/5\n"
            f"  Show simulation: {_state.show_simulation}\n"
            f"  Max scenarios: {_state.max_scenarios}"
        )

    if sub == "depth":
        if len(argv) < 2:
            return f"Current depth: {_state.depth}/5\nUsage: /doga depth <1-5>"
        try:
            d = int(argv[1])
            if d < 1 or d > 5:
                return "Depth must be between 1 and 5."
            _state.depth = d
            return f"DOGA depth set to {d}/5."
        except ValueError:
            return "Invalid number. Use /doga depth <1-5>."

    if sub == "show":
        _state.show_simulation = True
        return "DOGA simulation panel will be shown in responses."

    if sub == "hide":
        _state.show_simulation = False
        return "DOGA simulation panel hidden. Only final answer will be shown."

    return f"Unknown subcommand: {sub}\n\n{_DOGA_HELP.format(state=_state.to_dict())}"

# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("transform_llm_output", _on_transform_llm_output)
    ctx.register_hook("post_tool_call", _on_post_tool_call)

    ctx.register_tool(
        name="simulate",
        toolset="doga",
        schema=_SIMULATE_SCHEMA,
        handler=_simulate_tool_handler,
        check_fn=_check_simulate_requirements,
        description="Run Monte Carlo probability simulations over scenarios.",
        emoji="🎲",
    )

    ctx.register_command(
        "doga",
        handler=_handle_doga,
        description="Control DOGA probabilistic thinking.",
        args_hint="on|off|status|depth <1-5>|show|hide",
    )
