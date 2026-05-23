import doga.thinking_prompt as tp


def test_build_prompt_depth_1():
    prompt = tp.build_prompt(1)
    assert "Information" in prompt
    assert "Understanding" in prompt
    assert "Action" in prompt
    assert "scenario" not in prompt.lower()


def test_build_prompt_depth_2():
    prompt = tp.build_prompt(2)
    assert "Information" in prompt
    assert "scenario" not in prompt.lower()


def test_build_prompt_depth_3():
    prompt = tp.build_prompt(3)
    assert "scenario" in prompt.lower()
    assert "reason_deeper" in prompt


def test_build_prompt_depth_5():
    prompt = tp.build_prompt(5)
    assert "scenario" in prompt.lower()
    assert "reason_deeper" in prompt
    assert "simulate" in prompt


def test_build_goal_prompt_wrapper():
    result = tp.build_goal_prompt("test query", depth=3)
    assert result.startswith("\n\n[world_model_guide]")
    assert result.endswith("[/world_model_guide]")


def test_build_goal_prompt_hats():
    result = tp.build_goal_prompt("query", depth=5, hats_enabled=True)
    assert "[WHITE]" in result


def test_build_goal_prompt_no_hats():
    result = tp.build_goal_prompt("query", depth=5, hats_enabled=False)
    assert "[WHITE]" not in result


def test_build_goal_prompt_with_patterns():
    patterns = [{"goal_type": "Information", "count": 3}]
    result = tp.build_goal_prompt("query", depth=1, past_patterns=patterns)
    assert "Previous patterns" in result
