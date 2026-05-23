"""Tests for /doga slash commands."""
import doga.__init__ as plugin


def setup_method():
    plugin._state.enabled = True
    plugin._state.auto_depth = True
    plugin._state.depth = 3
    plugin._state.show_simulation = True
    plugin._state.de_bono_enabled = True
    plugin._state.max_recursion = 3
    plugin._state.memory_enabled = True


def test_help():
    result = plugin._handle_doga("help")
    assert "DOGA" in result
    assert "auto" in result


def test_help_empty():
    result = plugin._handle_doga("")
    assert "DOGA" in result


def test_on():
    plugin._state.enabled = False
    result = plugin._handle_doga("on")
    assert plugin._state.enabled is True
    assert "enabled" in result


def test_off():
    plugin._state.enabled = True
    result = plugin._handle_doga("off")
    assert plugin._state.enabled is False
    assert "disabled" in result


def test_status():
    result = plugin._handle_doga("status")
    assert "DOGA status" in result
    assert "Enabled" in result


def test_auto():
    plugin._state.auto_depth = False
    result = plugin._handle_doga("auto")
    assert plugin._state.auto_depth is True
    assert "auto" in result


def test_manual():
    result = plugin._handle_doga("manual high")
    assert plugin._state.auto_depth is False
    assert plugin._state.depth == 5


def test_manual_no_arg():
    result = plugin._handle_doga("manual")
    assert "Usage" in result


def test_manual_invalid():
    result = plugin._handle_doga("manual ultra")
    assert "Level must be" in result


def test_depth():
    result = plugin._handle_doga("depth 4")
    assert plugin._state.depth == 4
    assert plugin._state.auto_depth is False


def test_depth_no_arg():
    result = plugin._handle_doga("depth")
    assert "Current depth" in result


def test_depth_out_of_range():
    result = plugin._handle_doga("depth 6")
    assert "between 1 and 5" in result


def test_depth_invalid_number():
    result = plugin._handle_doga("depth abc")
    assert "Invalid number" in result


def test_show():
    plugin._state.show_simulation = False
    result = plugin._handle_doga("show")
    assert plugin._state.show_simulation is True
    assert "shown" in result


def test_hide():
    plugin._state.show_simulation = True
    result = plugin._handle_doga("hide")
    assert plugin._state.show_simulation is False
    assert "hidden" in result


def test_hats_on():
    plugin._state.de_bono_enabled = False
    result = plugin._handle_doga("hats on")
    assert plugin._state.de_bono_enabled is True


def test_hats_off():
    plugin._state.de_bono_enabled = True
    result = plugin._handle_doga("hats off")
    assert plugin._state.de_bono_enabled is False
    assert plugin._state._active_hats == []


def test_hats_no_arg():
    result = plugin._handle_doga("hats")
    assert "Usage" in result


def test_max_recursion():
    result = plugin._handle_doga("max_recursion 5")
    assert plugin._state.max_recursion == 5


def test_max_recursion_no_arg():
    result = plugin._handle_doga("max_recursion")
    assert "Current max recursion" in result


def test_max_recursion_out_of_range():
    result = plugin._handle_doga("max_recursion 0")
    assert "between 1 and 5" in result


def test_max_recursion_invalid():
    result = plugin._handle_doga("max_recursion abc")
    assert "Invalid number" in result


def test_memory_on():
    plugin._state.memory_enabled = False
    from unittest.mock import patch
    with patch.object(plugin, "MNEMOSYNE_AVAILABLE", True):
        result = plugin._handle_doga("memory on")
    assert plugin._state.memory_enabled is True


def test_memory_off():
    plugin._state.memory_enabled = True
    result = plugin._handle_doga("memory off")
    assert plugin._state.memory_enabled is False


def test_memory_no_arg():
    result = plugin._handle_doga("memory")
    assert "Usage" in result


def test_unknown():
    result = plugin._handle_doga("blahblah")
    assert "Unknown subcommand" in result


def test_status_with_memory_disabled():
    plugin._state.memory_enabled = False
    result = plugin._handle_doga("status")
    assert "Memory: False" in result or "Memory: disabled" in result or "Memory: False" in result
