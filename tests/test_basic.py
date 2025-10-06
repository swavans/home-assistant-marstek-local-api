"""Simple test to verify pytest setup works."""

def test_pytest_setup():
    """Test that pytest is working."""
    assert 1 + 1 == 2

def test_pytest_with_mock():
    """Test that mocking works."""
    from unittest.mock import Mock
    mock_obj = Mock()
    mock_obj.test_method.return_value = "test"
    assert mock_obj.test_method() == "test"

def test_homeassistant_imports():
    """Test that Home Assistant imports work."""
    from homeassistant.const import CONF_HOST, CONF_PORT
    assert CONF_HOST == "host"
    assert CONF_PORT == "port"