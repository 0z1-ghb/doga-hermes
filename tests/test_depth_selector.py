import doga.depth_selector as ds


def test_empty():
    assert ds.assess_complexity("") == "low"
    assert ds.assess_complexity("   ") == "low"
    assert ds.assess_complexity(None) == "low"


def test_greeting():
    text = "merhaba"
    assert ds.assess_complexity(text) == "low"


def test_greeting_english():
    text = "hello"
    assert ds.assess_complexity(text) == "low"


def test_short_analysis():
    text = "risk?"
    assert ds.assess_complexity(text) == "low"


def test_medium():
    text = "risk analizi, karşılaştır"
    assert ds.assess_complexity(text) == "medium"


def test_high():
    text = "belki, acaba, risk analizi, karşılaştır, endişeleniyorum, strateji"
    assert ds.assess_complexity(text) == "high"


def test_turkish_markers():
    text = "akıllı sözleşme risk analizi ve güvenlik"
    assert ds.assess_complexity(text) == "medium"


def test_long_text():
    text = " ".join(["kelime"] * 31)
    assert ds.assess_complexity(text) == "medium"


def test_long_text_with_markers():
    text = ("belki " * 5) + ("risk " * 5) + ("endişe " * 5)
    assert ds.assess_complexity(text) == "high"


def test_complexity_to_depth():
    assert ds.complexity_to_depth("low") == 1
    assert ds.complexity_to_depth("medium") == 3
    assert ds.complexity_to_depth("high") == 5


def test_complexity_to_depth_invalid():
    assert ds.complexity_to_depth("unknown") == 3
