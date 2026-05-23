import doga.output_formatter as fmt


def test_strip_guide_closed():
    text = "before [world_model_guide]guide[/world_model_guide] after"
    assert fmt._strip_guide_blocks(text) == "before  after"


def test_strip_guide_unclosed():
    text = "before [world_model_guide]guide text after"
    assert fmt._strip_guide_blocks(text) == "before"


def test_strip_guide_none():
    text = "hello world"
    assert fmt._strip_guide_blocks(text) == "hello world"


def test_extract_wm_closed():
    text = "a <world_model>inner</world_model> b"
    blocks, remaining = fmt._extract_world_model(text)
    assert blocks == ["inner"]
    assert remaining == "a  b"


def test_extract_wm_unclosed():
    text = "a <world_model>inner text"
    blocks, remaining = fmt._extract_world_model(text)
    assert blocks == []
    assert "inner text" in remaining


def test_extract_wm_unclosed_multiple():
    text = "a <world_model>first\n<world_model>second"
    blocks, remaining = fmt._extract_world_model(text)
    assert blocks == []
    assert "<world_model>" not in remaining


def test_extract_wm_mixed_one_closed_one_unclosed():
    text = "<world_model>closed</world_model> between <world_model>open"
    blocks, remaining = fmt._extract_world_model(text)
    assert blocks == ["closed"]
    assert "<world_model>open" in remaining


def test_extract_wm_none():
    text = "no tags here"
    blocks, remaining = fmt._extract_world_model(text)
    assert blocks == []
    assert remaining == "no tags here"


def test_detect_level_explicit():
    tagged = fmt._detect_level_blocks(["Level 2 content"])
    assert tagged == [(2, "Level 2 content")]


def test_detect_level_ignorecase():
    tagged = fmt._detect_level_blocks(["LEVEL 3 content"])
    assert tagged == [(3, "LEVEL 3 content")]


def test_detect_level_recursion():
    tagged = fmt._detect_level_blocks(["--- RECURSION LEVEL 4 ---"])
    assert tagged == [(4, "--- RECURSION LEVEL 4 ---")]


def test_detect_level_sequential():
    tagged = fmt._detect_level_blocks(["a", "b", "c"])
    assert tagged == [(1, "a"), (2, "b"), (3, "c")]


def test_format_panel_multi_level():
    panel = fmt._format_simulation_panel(
        ["Level 1 analysis", "Level 2 deeper"],
        active_hats=["white", "black"],
    )
    assert "Thinking Process" in panel
    assert "White, Black" in panel
    assert "Level 2" in panel


def test_format_panel_no_hats():
    panel = fmt._format_simulation_panel(["content"])
    assert "Thinking Process" in panel


def test_format_panel_empty():
    assert fmt._format_simulation_panel([""]) == ""


def test_format_response_no_simulation():
    result = fmt.format_response("some response", show_simulation=False)
    assert result == "some response"


def test_format_response_no_blocks():
    result = fmt.format_response("hello world", show_simulation=True)
    assert result == "hello world"


def test_format_response_with_panel():
    result = fmt.format_response(
        "<world_model>thinking</world_model>\nanswer",
        show_simulation=True,
    )
    assert "Thinking Process" in result
    assert "answer" in result
    assert "Response" in result


def test_format_response_mixed_tags():
    result = fmt.format_response(
        "<world_model>closed</world_model>\nbetween\n<world_model>open",
        show_simulation=True,
    )
    assert "Thinking Process" in result
    assert "between" in result
    assert "<world_model>" not in result
