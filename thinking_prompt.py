"""Goal detection and scenario generation prompt templates for DOGA.

These are injected into the user message via the ``pre_llm_call`` hook
to guide the LLM toward probabilistic, goal-aware thinking.
"""

from __future__ import annotations

from typing import Optional

from . import de_bono_hats

# ---------------------------------------------------------------------------
# Goal detection — the "why" before the "what"
# ---------------------------------------------------------------------------

GOAL_DETECTION_PROMPT = """\
Before answering, briefly identify what the user's primary need is:

- **Information**: They want factual data, analysis, or explanation.
- **Understanding**: They want to feel heard, validated, or understood.
- **Action**: They want a decision, recommendation, or next step.

Choose the dominant goal and let it shape your response.
"""

# ---------------------------------------------------------------------------
# Probabilistic thinking — scenario enumeration + weighing
# ---------------------------------------------------------------------------

SCENARIO_PROMPT_TEMPLATE = """\
Consider multiple possible scenarios or interpretations of this question.
For each scenario, think about:
1. What would need to be true for this scenario to hold?
2. How likely is it relative to the alternatives?
3. What would change if this scenario is wrong?

Use the `<world_model>` tag for your internal reasoning, like:
<world_model>
## Scenarios
1. **Scenario A** — what it assumes, rough likelihood
2. **Scenario B** — what it assumes, rough likelihood
3. **Scenario C** — what it assumes, rough likelihood
</world_model>

If you can identify specific variables with probabilities, call the
`simulate` tool to run a Monte Carlo analysis.
"""

# ---------------------------------------------------------------------------
# Simulation tool guidance — how to use the simulate tool
# ---------------------------------------------------------------------------

SIMULATION_TOOL_GUIDANCE = """\
You have access to the `simulate` tool for quantitative probability analysis.
Call it when you need to weigh multiple factors with uncertainty:

Example:
```json
{
  "scenarios": [
    {
      "name": "contract_valid",
      "variables": {"signature_authorized": 0.8, "no_duress": 0.95},
      "conditions": ["signature_authorized and no_duress"]
    },
    {
      "name": "contract_invalid",
      "variables": {"signature_authorized": 0.2, "duress": 0.15},
      "conditions": ["not signature_authorized or duress"]
    }
  ],
  "n_iterations": 10000
}
```

The tool returns probability distributions. Use these to support your reasoning.
"""

# ---------------------------------------------------------------------------
# Depth levels
# ---------------------------------------------------------------------------

# Depth 1–2: lightweight (just goal awareness)
LIGHT_PROMPT = GOAL_DETECTION_PROMPT

# Depth 3–4: goal + scenarios
MEDIUM_PROMPT = f"""\
{GOAL_DETECTION_PROMPT}

{SCENARIO_PROMPT_TEMPLATE}
"""

# Depth 5: full probabilistic reasoning
DEEP_PROMPT = f"""\
{GOAL_DETECTION_PROMPT}

{SCENARIO_PROMPT_TEMPLATE}

{SIMULATION_TOOL_GUIDANCE}
"""


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_prompt(depth: int = 3) -> str:
    """Return the appropriate prompt text for the given depth (1–5)."""
    if depth <= 2:
        return LIGHT_PROMPT
    elif depth <= 4:
        return MEDIUM_PROMPT
    else:
        return DEEP_PROMPT


def build_goal_prompt(
    user_message: str,
    depth: int = 3,
    past_patterns: Optional[list] = None,
    hats_enabled: bool = True,
) -> str:
    """Build a complete thinking guidance block for injection.

    Optionally includes past goal patterns from memory and De Bono
    parallel thinking hats for structured reasoning.
    This is the main entry point called from ``pre_llm_call``.
    """
    prompt = build_prompt(depth)

    if hats_enabled:
        prompt += de_bono_hats.build_hat_guidance(depth)

    if past_patterns:
        lines = ["", "Previous patterns for similar queries:"]
        for p in past_patterns:
            lines.append(f"- Goal: {p.get('goal_type', '?')} (used {p.get('count', 1)}x)")
        prompt += "\n" + "\n".join(lines)

    return f"\n\n[world_model_guide]\n{prompt}\n[/world_model_guide]"
