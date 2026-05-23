"""Monte Carlo simulation engine for DOGA plugin."""

from __future__ import annotations

import ast
import functools
import math
import random
from typing import Any, Dict, List, Optional


class _ConditionCache:
    """Cache compiled condition expressions."""

    def __init__(self):
        self._cache: Dict[str, callable] = {}

    def get(self, expr: str) -> callable:
        if expr not in self._cache:
            self._cache[expr] = self._compile(expr)
        return self._cache[expr]

    @staticmethod
    def _compile(expr: str) -> callable:
        """Compile a boolean expression into a callable once.

        Uses AST whitelist approach instead of raw eval for safety.
        """
        allowed_types = {
            ast.Expression, ast.BoolOp, ast.And, ast.Or,
            ast.UnaryOp, ast.Not,
            ast.Name, ast.Constant,
            ast.Compare, ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE,
            ast.In, ast.NotIn,
        }
        try:
            tree = ast.parse(expr, mode="eval")
            if not all(isinstance(n, tuple(allowed_types)) for n in ast.walk(tree)):
                return lambda _vars: False
            code = compile(tree, "<doga_cond>", "eval")
        except (SyntaxError, ValueError):
            return lambda _vars: False

        def _call(variables: Dict[str, bool]) -> bool:
            safe = {k: v for k, v in variables.items() if k.isidentifier()}
            try:
                return bool(eval(code, {"__builtins__": {}}, safe))
            except Exception:
                return False

        return _call


_COND_CACHE = _ConditionCache()


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

        # Pre-compile condition expressions once
        parsed = []
        for sc in scenarios:
            name = sc.get("name", "unnamed")
            variables = dict(sc.get("variables", {}))
            conditions = list(sc.get("conditions", []))
            compiled = [_COND_CACHE.get(c) for c in conditions]
            parsed.append((name, variables, conditions, compiled))

        counts: Dict[str, int] = {p[0]: 0 for p in parsed}
        none_count = 0

        for _ in range(n_iterations):
            all_vars: Dict[str, bool] = {}
            for _, variables, _, _ in parsed:
                for var, prob in variables.items():
                    if var not in all_vars:
                        all_vars[var] = self._rng.random() < prob

            matched = False
            for name, variables, _conditions, compiled in parsed:
                if not _conditions:
                    if not variables:
                        counts[name] = counts.get(name, 0) + 1
                        matched = True
                    else:
                        scenario_vars = {k: v for k, v in all_vars.items() if k in variables}
                        if scenario_vars and all(scenario_vars.values()):
                            counts[name] = counts.get(name, 0) + 1
                            matched = True
                else:
                    ok = all(call(all_vars) for call in compiled)
                    if ok:
                        counts[name] = counts.get(name, 0) + 1
                        matched = True

            if not matched:
                none_count += 1

        total = n_iterations
        result_scenarios = []
        for name, _, _, _ in parsed:
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
