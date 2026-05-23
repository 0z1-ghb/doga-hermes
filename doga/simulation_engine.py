"""Monte Carlo simulation engine for DOGA plugin."""

from __future__ import annotations

import ast
import math
import random
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Condition cache — compile-once safe expression evaluator
# ---------------------------------------------------------------------------

class _ConditionCache:
    """Cache compiled condition expressions with bounded size and thread safety."""

    _MAX_SIZE = 1024

    def __init__(self):
        self._cache: Dict[str, callable] = {}
        self._lock = threading.Lock()

    def get(self, expr: str) -> callable:
        with self._lock:
            if expr in self._cache:
                return self._cache[expr]
            if len(self._cache) >= self._MAX_SIZE:
                self._cache.clear()
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
            ast.Name, ast.Constant, ast.Load,
            ast.Compare, ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE,
            ast.In, ast.NotIn,
        }
        try:
            tree = ast.parse(expr, mode="eval")
            if not all(isinstance(n, tuple(allowed_types)) for n in ast.walk(tree)):
                return lambda _vars: False
            code = compile(tree, "<doga_cond>", "eval")
        except (SyntaxError, ValueError, RecursionError):
            return lambda _vars: False

        def _call(variables: Dict[str, bool]) -> bool:
            safe = {k: v for k, v in variables.items() if k.isidentifier()}
            try:
                return bool(eval(code, {"__builtins__": {}}, safe))
            except Exception:
                return False

        return _call


_COND_CACHE = _ConditionCache()


# ---------------------------------------------------------------------------
# Scenario data structure — flat for Phase 2, children ready for Phase 3
# ---------------------------------------------------------------------------

@dataclass
class _Scenario:
    """Internal representation of a single scenario for simulation."""

    name: str
    variables: Dict[str, float] = field(default_factory=dict)
    raw_conditions: List[str] = field(default_factory=list, repr=False)
    compiled_conditions: List[callable] = field(default_factory=list, repr=False, compare=False)
    children: List[_Scenario] = field(default_factory=list, repr=False, compare=False)


def _build_scenario(raw: Dict[str, Any]) -> _Scenario:
    """Convert a raw dict from the LLM into a _Scenario."""
    return _Scenario(
        name=raw.get("name", "unnamed"),
        variables=dict(raw.get("variables", {})),
        raw_conditions=list(raw.get("conditions", [])),
        compiled_conditions=[_COND_CACHE.get(c) for c in raw.get("conditions", [])],
        children=[_build_scenario(ch) for ch in raw.get("children", [])],
    )


def _evaluate_scenario(sc: _Scenario, all_vars: Dict[str, bool]) -> bool:
    """Check whether a scenario matches the current sampled variables."""
    if not sc.raw_conditions:
        if not sc.variables:
            return True
        scenario_vars = {k: v for k, v in all_vars.items() if k in sc.variables}
        return bool(scenario_vars and all(scenario_vars.values()))
    return all(fn(all_vars) for fn in sc.compiled_conditions)


def _evaluate_children(
    sc: _Scenario,
    inherited_vars: Dict[str, bool],
    counts: Dict[str, int],
    rng: random.Random,
) -> None:
    """Recursively evaluate children with scoped variable space."""
    for child in sc.children:
        scoped_vars = dict(inherited_vars)
        for var, prob in child.variables.items():
            scoped_vars[var] = rng.random() < prob
        if _evaluate_scenario(child, scoped_vars):
            counts[child.name] = counts.get(child.name, 0) + 1
            _evaluate_children(child, scoped_vars, counts, rng)


def _collect_names(sc: _Scenario, names: set[str]) -> None:
    """Recursively collect all scenario names into the set."""
    for child in sc.children:
        names.add(child.name)
        _collect_names(child, names)


# ---------------------------------------------------------------------------
# Monte Carlo engine
# ---------------------------------------------------------------------------

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
          - ``children``: list[dict] (optional, Phase 3) — nested sub-scenarios.

        Returns ``{"scenarios": [...], "summary": {...}}``.
        """
        if not scenarios:
            return {"scenarios": [], "summary": {"total_iterations": 0}}

        parsed = [_build_scenario(sc) for sc in scenarios]
        counts: Dict[str, int] = {s.name: 0 for s in parsed}
        none_count = 0

        # Collect all names including children for results
        all_names: set[str] = set(counts.keys())
        for sc in parsed:
            _collect_names(sc, all_names)
        for name in all_names:
            counts.setdefault(name, 0)

        for _ in range(n_iterations):
            all_vars: Dict[str, bool] = {}
            for sc in parsed:
                for var, prob in sc.variables.items():
                    if var not in all_vars:
                        all_vars[var] = self._rng.random() < prob

            matched = False
            for sc in parsed:
                if _evaluate_scenario(sc, all_vars):
                    counts[sc.name] = counts.get(sc.name, 0) + 1
                    matched = True
                    # Also evaluate children conditional on parent match
                    _evaluate_children(sc, all_vars, counts, self._rng)

            if not matched:
                none_count += 1

        total = n_iterations
        result_scenarios = []
        for name in sorted(all_names):
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
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def estimate_from_description(description: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": "base_case",
                "variables": {"likelihood": 0.5},
                "conditions": [],
            }
        ]


# Module-level convenience — each call creates a fresh engine
# to guarantee thread safety (no shared RNG state)


def run_scenarios(
    scenarios: List[Dict[str, Any]],
    n_iterations: int = 10000,
) -> Dict[str, Any]:
    engine = MonteCarloEngine(seed=42)
    return engine.simulate(scenarios, n_iterations=n_iterations)
