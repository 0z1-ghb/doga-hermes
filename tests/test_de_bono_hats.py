import doga.de_bono_hats as hats


def test_hats_for_depth_1():
    assert hats.hats_for_depth(1) == ["white"]


def test_hats_for_depth_2():
    assert hats.hats_for_depth(2) == ["white", "black"]


def test_hats_for_depth_3():
    assert hats.hats_for_depth(3) == ["white", "black", "yellow"]


def test_hats_for_depth_4():
    assert hats.hats_for_depth(4) == ["white", "black", "yellow", "green"]


def test_hats_for_depth_5():
    assert hats.hats_for_depth(5) == ["white", "black", "yellow", "green", "red"]


def test_hats_for_depth_invalid():
    assert hats.hats_for_depth(0) == []
    assert hats.hats_for_depth(6) == []


def test_hats_for_recursion_level_1():
    assert hats.hats_for_recursion_level(1) == ["white", "black", "yellow"]


def test_hats_for_recursion_level_3():
    assert hats.hats_for_recursion_level(3) == ["red", "green"]


def test_hats_for_recursion_level_5():
    assert hats.hats_for_recursion_level(5) == ["white", "red"]


def test_hats_for_recursion_level_default():
    assert hats.hats_for_recursion_level(99) == ["white", "black"]


def test_build_hat_guidance_depth_5():
    text = hats.build_hat_guidance(5)
    assert "[WHITE]" in text
    assert "[BLACK]" in text
    assert "[YELLOW]" in text
    assert "[GREEN]" in text
    assert "[RED]" in text


def test_build_hat_guidance_invalid():
    assert hats.build_hat_guidance(0) == ""


def test_format_hats_header():
    assert hats.format_hats_header(["white", "black"]) == " - White, Black"


def test_format_hats_header_empty():
    assert hats.format_hats_header([]) == ""
