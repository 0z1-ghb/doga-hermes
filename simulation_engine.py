"""Monte Carlo simulation engine for DOGA plugin."""

from __future__ import annotations

import random
import statistics
import math
from typing import Any, Dict, List, Optional, Tuple


class MonteCarloEngine:
    """Lightweight Monte Carlo simulator.

    Runs N iterations over a set of scenarios with probabilistic variables
    and returns the likelihood of each scenario.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def simulate(
        self,
        scenarios: List[Dict[str, Any]],
        n_iterations: int = 10000,
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation over a list of scenarios.

        Each scenario dict should have:
          - ``name``: str — scenario label
          - ``variables``: dict[str, float] — variable name → P(true) in [0,1]
          - ``conditions``: list[str] (optional) — Python expressions like
            ``"imza_var and not baskı"`` that must be True for this scenario.

        Returns ``{"scenarios": [...], "summary": {...}}``.
        """
        if not scenarios:
            return {"scenarios": [], "summary": {"total_iterations": 0}}

        # Normalise variable names so conditions can reference them
        parsed = []
        for sc in scenarios:
            name = sc.get("name", "unnamed")
            variables = dict(sc.get("variables", {}))
            conditions = list(sc.get("conditions", []))
            parsed.append((name, variables, conditions))

        counts: Dict[str, int] = {p[0]: 0 for p in parsed}
        none_count = 0

        for _ in range(n_iterations):
            # Sample all variables across all scenarios (union of var names)
            all_vars: Dict[str, bool] = {}
            for _, variables, _ in parsed:
                for var, prob in variables.items():
                    if var not in all_vars:
                        all_vars[var] = self._rng.random() < prob

            # Check which scenario conditions match
            matched = False
            for name, variables, conditions in parsed:
                if not conditions:
                    # No conditions: check if all variables are True
                    scenario_vars = {k: v for k, v in all_vars.items() if k in variables}
                    if scenario_vars and all(scenario_vars.values()):
                        counts[name] = counts.get(name, 0) + 1
                        matched = True
                else:
                    # Evaluate Python expressions
                    try:
                        ok = all(
                            self._eval_condition(cond, all_vars)
                            for cond in conditions
                        )
                        if ok:
                            counts[name] = counts.get(name, 0) + 1
                            matched = True
                    except Exception:
                        continue

            if not matched:
                none_count += 1

        total = n_iterations
        result_scenarios = []
        for name, _, _ in parsed:
            prob = counts.get(name, 0) / total if total > 0 else 0.0
            result_scenarios.append({
                "name": name,
                "probability": round(prob, 4),
                "samples": counts.get(name, 0),
            })

        none_prob = none_count / total if total > 0 else 0.0
        if none_prob > 0:
            result_scenarios.append({
                "name": "__unmatched__",
                "probability": round(none_prob, 4),
                "samples": none_count,
            })

        result_scenarios.sort(key=lambda x: x["probability"], reverse=True)

        most_likely = result_scenarios[0] if result_scenarios else None
        entropy = self._compute_entropy([s["probability"] for s in result_scenarios])

        return {
            "scenarios": result_scenarios,
            "summary": {
                "total_iterations": total,
                "most_likely": most_likely["name"] if most_likely else None,
                "most_likely_probability": most_likely["probability"] if most_likely else 0.0,
                "entropy": round(entropy, 4),
                "uncertainty": "high" if entropy > 1.5 else ("medium" if entropy > 0.5 else "low"),
            },
        }

    def _eval_condition(self, expr: str, variables: Dict[str, bool]) -> bool:
        """Safely evaluate a boolean expression like ``imza_var and not baskı``."""
        # Build a safe local namespace with only the known variables
        safe_locals = {}
        for k, v in variables.items():
            # Only allow alphanumeric + underscore variable names
            if k.isidentifier():
                safe_locals[k] = v
        try:
            return bool(eval(expr, {"__builtins__": {}}, safe_locals))
        except Exception:
            return False

    def _compute_entropy(self, probabilities: List[float]) -> float:
        """Shannon entropy of a probability distribution."""
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def estimate_from_description(description: str) -> List[Dict[str, Any]]:
        """Simple heuristic to convert a text description to scenario variables.

        This is a fallback for when the LLM doesn't provide structured data.
        Returns a single generic scenario with equal probabilities."""
        return [
            {
                "name": "base_case",
                "variables": {"likelihood": 0.5},
                "conditions": [],
            }
        ]


# Module-level convenience
_default_engine = MonteCarloEngine(seed=42)


def run_scenarios(
    scenarios: List[Dict[str, Any]],
    n_iterations: int = 10000,
) -> Dict[str, Any]:
    """Run Monte Carlo simulation (convenience wrapper)."""
    return _default_engine.simulate(scenarios, n_iterations=n_iterations)
