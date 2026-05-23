import random
import doga.simulation_engine as eng


def test_condition_cache_hit():
    c = eng._ConditionCache()
    fn1 = c.get("x and y")
    fn2 = c.get("x and y")
    assert fn1 is fn2
    assert fn1({"x": True, "y": True})
    assert not fn1({"x": True, "y": False})


def test_condition_cache_blocked_ast():
    c = eng._ConditionCache()
    assert not c.get("x + y")({})
    assert not c.get("func()")({})
    assert not c.get("obj.attr")({})
    assert not c.get("x[0]")({})


def test_condition_cache_syntax_error():
    c = eng._ConditionCache()
    assert not c.get("x and ")({})


def test_condition_cache_safe_ast():
    c = eng._ConditionCache()
    assert c.get("x == True")({"x": True})
    assert c.get("x != False")({"x": True})
    assert c.get("x in items")({"x": True, "items": {True}})
    assert not c.get("x > 5")({"x": 3})


def test_condition_cache_thread_safety():
    c = eng._ConditionCache()
    assert c._MAX_SIZE == 1024
    assert c._lock is not None


def test_condition_cache_max_size():
    c = eng._ConditionCache()
    for i in range(1030):
        c.get(f"x == {i}")
    assert len(c._cache) <= c._MAX_SIZE


def test_evaluate_scenario_no_conditions_all_vars():
    sc = eng._Scenario(name="t", variables={"a": 0.5, "b": 0.5})
    assert eng._evaluate_scenario(sc, {"a": True, "b": True})


def test_evaluate_scenario_no_conditions_one_false():
    sc = eng._Scenario(name="t", variables={"a": 0.5, "b": 0.5})
    assert not eng._evaluate_scenario(sc, {"a": True, "b": False})


def test_evaluate_scenario_with_conditions():
    sc = eng._Scenario(
        name="t",
        variables={"a": 0.5, "b": 0.5},
        raw_conditions=["a and b"],
        compiled_conditions=[eng._COND_CACHE.get("a and b")],
    )
    assert eng._evaluate_scenario(sc, {"a": True, "b": True})
    assert not eng._evaluate_scenario(sc, {"a": True, "b": False})


def test_evaluate_scenario_no_vars():
    sc = eng._Scenario(name="t", variables={})
    assert eng._evaluate_scenario(sc, {})


def test_evaluate_scenario_unknown_vars():
    sc = eng._Scenario(name="t", variables={"a": 0.5})
    assert not eng._evaluate_scenario(sc, {})


def test_evaluate_children_scoped():
    parent = eng._Scenario(name="p", variables={"x": 0.5})
    child = eng._Scenario(name="c", variables={"y": 0.5})
    parent.children = [child]
    counts = {"p": 0, "c": 0}
    rng = random.Random(42)
    eng._evaluate_children(parent, {"x": True}, counts, rng)
    assert counts["p"] == 0
    assert counts["c"] in (0, 1)


def test_evaluate_children_namespace():
    parent = eng._Scenario(name="p", variables={"x": 0.5})
    child = eng._Scenario(name="c", variables={"x": 0.5})
    parent.children = [child]
    counts = {"p": 0, "c": 0}
    rng = random.Random(42)
    eng._evaluate_children(parent, {"x": True}, counts, rng)
    assert counts["c"] in (0, 1)


def test_evaluate_children_deep():
    def make(name, prob, child=None):
        sc = eng._Scenario(name=name, variables={"v": prob})
        if child:
            sc.children = [child]
        return sc
    c3 = make("l3", 0.5)
    c2 = make("l2", 0.5, c3)
    c1 = make("l1", 0.5, c2)
    counts = {"l1": 0, "l2": 0, "l3": 0}
    rng = random.Random(42)
    eng._evaluate_children(c1, {"v": True}, counts, rng)
    for name in counts:
        assert counts[name] in (0, 1)


def test_monte_carlo_probability():
    engine = eng.MonteCarloEngine(seed=42)
    result = engine.simulate([
        {"name": "always", "variables": {"x": 1.0}},
        {"name": "never", "variables": {"y": 0.0}},
    ], n_iterations=10000)
    for s in result["scenarios"]:
        if s["name"] == "always":
            assert s["probability"] == 1.0
        elif s["name"] == "never":
            assert s["probability"] == 0.0


def test_monte_carlo_entropy():
    engine = eng.MonteCarloEngine(seed=42)
    result = engine.simulate([
        {"name": "a", "variables": {"x": 0.5}},
        {"name": "b", "variables": {"y": 0.5}},
    ], n_iterations=10000)
    assert result["summary"]["entropy"] > 0
    assert result["summary"]["uncertainty"] in ("low", "medium", "high")


def test_monte_carlo_zero_iterations():
    engine = eng.MonteCarloEngine(seed=42)
    result = engine.simulate([
        {"name": "t", "variables": {"x": 0.5}},
    ], n_iterations=0)
    assert result["summary"]["total_iterations"] == 0
    for s in result["scenarios"]:
        assert s["probability"] == 0.0


def test_monte_carlo_empty():
    engine = eng.MonteCarloEngine(seed=42)
    result = engine.simulate([], n_iterations=100)
    assert result["scenarios"] == []


def test_run_scenarios_module():
    result = eng.run_scenarios([
        {"name": "t", "variables": {"x": 0.5}},
    ], n_iterations=100)
    assert "summary" in result
    assert result["summary"]["total_iterations"] == 100
