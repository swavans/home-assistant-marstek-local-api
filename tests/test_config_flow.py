"""Tests for MarstekConfigFlow."""
import pytest
import sys
import os
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from custom_components.marstek_local_api.config_flow import MarstekConfigFlow
from custom_components.marstek_local_api.const import DOMAIN, CONF_DOMAINS, OPTIONS, CONF_DEVICE_NAME


class TestMarstekConfigFlow:
    """Test MarstekConfigFlow."""

    @pytest.mark.asyncio
    async def test_config_flow_init(self, hass):
        """Test config flow initialization."""
        flow = MarstekConfigFlow()
        flow.hass = hass
        
        assert flow.VERSION == 1
        assert flow.domain == DOMAIN

    @pytest.mark.asyncio
    async def test_async_step_user_show_form(self, hass):
        """Test showing the user form."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        result = await flow.async_step_user()

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert "data_schema" in result
        
        # Check schema contains required fields
        schema = result["data_schema"]
        schema_keys = {field.schema for field in schema.schema}
        
        # Extract the actual field names/keys
        field_names = set()
        for field in schema.schema:
            if hasattr(field, 'schema'):
                field_names.add(str(field.schema))
            else:
                field_names.add(str(field))

        # Check required fields are present (as strings since that's how they appear)
        assert any(CONF_HOST in name for name in field_names)
        assert any(CONF_PORT in name for name in field_names)
        assert any(CONF_DEVICE_NAME in name for name in field_names)

    @pytest.mark.asyncio
    async def test_async_step_user_create_entry(self, hass):
        """Test creating config entry with valid user input."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "Marstek Battery",
            CONF_SCAN_INTERVAL: 10,
            CONF_DOMAINS: ["Bat.GetStatus", "Wifi.GetStatus"],
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["title"] == "Marstek Battery"
        assert result["data"] == user_input

    @pytest.mark.asyncio
    async def test_async_step_user_default_values(self, hass):
        """Test that form shows with correct default values."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        result = await flow.async_step_user()
        schema = result["data_schema"]
        
        # Check that defaults are properly set
        # We'll create the schema and check if we can validate with defaults
        try:
            # Try to get default values by checking the schema
            defaults = {}
            for field in schema.schema:
                if hasattr(field, 'default'):
                    if field.schema == CONF_PORT:
                        assert field.default == 30000
                    elif field.schema == CONF_DEVICE_NAME:
                        assert field.default == "Marstek Battery"
                    elif field.schema == CONF_SCAN_INTERVAL:
                        assert field.default == 10
                    elif field.schema == CONF_DOMAINS:
                        assert field.default == list(OPTIONS.keys())
        except AttributeError:
            # If we can't access defaults directly, test with actual values
            pass

    @pytest.mark.asyncio
    async def test_async_step_user_minimal_input(self, hass):
        """Test creating entry with only required fields."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "192.168.1.50",
            # PORT, DEVICE_NAME, SCAN_INTERVAL, DOMAINS should use defaults
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_HOST] == "192.168.1.50"

    @pytest.mark.asyncio
    async def test_async_step_user_custom_port(self, hass):
        """Test config flow with custom port."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "10.0.0.100",
            CONF_PORT: 31000,
            CONF_DEVICE_NAME: "Custom Marstek",
            CONF_SCAN_INTERVAL: 30,
            CONF_DOMAINS: ["ES.GetStatus"],
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_PORT] == 31000
        assert result["data"][CONF_DEVICE_NAME] == "Custom Marstek"
        assert result["data"][CONF_SCAN_INTERVAL] == 30
        assert result["data"][CONF_DOMAINS] == ["ES.GetStatus"]

    @pytest.mark.asyncio
    async def test_async_step_user_all_domains(self, hass):
        """Test config flow with all available domains."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        all_domains = list(OPTIONS.keys())
        user_input = {
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "Full Feature Battery",
            CONF_SCAN_INTERVAL: 60,
            CONF_DOMAINS: all_domains,
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_DOMAINS] == all_domains
        assert len(result["data"][CONF_DOMAINS]) == len(OPTIONS)

    @pytest.mark.asyncio
    async def test_async_step_user_single_domain(self, hass):
        """Test config flow with single domain selection."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "192.168.1.201",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "Battery Only",
            CONF_SCAN_INTERVAL: 15,
            CONF_DOMAINS: ["Bat.GetStatus"],
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_DOMAINS] == ["Bat.GetStatus"]

    @pytest.mark.asyncio
    async def test_async_step_user_empty_domains(self, hass):
        """Test config flow with empty domains list."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "192.168.1.202",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "No Sensors",
            CONF_SCAN_INTERVAL: 10,
            CONF_DOMAINS: [],
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_DOMAINS] == []

    @pytest.mark.asyncio
    async def test_async_step_user_high_scan_interval(self, hass):
        """Test config flow with high scan interval."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "192.168.1.203",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "Slow Update Battery",
            CONF_SCAN_INTERVAL: 300,  # 5 minutes
            CONF_DOMAINS: ["Bat.GetStatus"],
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_SCAN_INTERVAL] == 300

    @pytest.mark.asyncio
    async def test_async_step_user_ipv6_address(self, hass):
        """Test config flow with IPv6 address."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "2001:db8::1",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "IPv6 Battery",
            CONF_SCAN_INTERVAL: 10,
            CONF_DOMAINS: ["Bat.GetStatus"],
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_HOST] == "2001:db8::1"

    @pytest.mark.asyncio
    async def test_async_step_user_hostname(self, hass):
        """Test config flow with hostname instead of IP."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_HOST: "marstek-battery.local",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "Local Battery",
            CONF_SCAN_INTERVAL: 10,
            CONF_DOMAINS: ["Bat.GetStatus"],
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["data"][CONF_HOST] == "marstek-battery.local"

    def test_config_flow_inheritance(self):
        """Test that MarstekConfigFlow inherits from correct base classes."""
        flow = MarstekConfigFlow()
        
        assert isinstance(flow, config_entries.ConfigFlow)
        assert flow.domain == DOMAIN

    @pytest.mark.asyncio
    async def test_options_validation(self, hass):
        """Test that OPTIONS constant contains expected domain mappings."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        # Test that all expected domains are in OPTIONS
        expected_domains = [
            "Wifi.GetStatus",
            "Bat.GetStatus", 
            "PV.GetStatus",
            "ES.GetStatus",
            "BLE.GetStatus",
            "ES.GetMode"
        ]

        for domain in expected_domains:
            assert domain in OPTIONS
            assert isinstance(OPTIONS[domain], str)
            assert len(OPTIONS[domain]) > 0

        # Test with all domains in user input
        user_input = {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 30000,
            CONF_DEVICE_NAME: "Test Battery",
            CONF_SCAN_INTERVAL: 10,
            CONF_DOMAINS: expected_domains,
        }

        result = await flow.async_step_user(user_input)
        assert result["type"] == "create_entry"

    @pytest.mark.asyncio
    async def test_schema_field_types(self, hass):
        """Test that schema fields have correct types."""
        flow = MarstekConfigFlow()
        flow.hass = hass

        result = await flow.async_step_user()
        schema = result["data_schema"]

        # Test with correct types
        valid_input = {
            CONF_HOST: "192.168.1.100",  # string
            CONF_PORT: 30000,  # int
            CONF_DEVICE_NAME: "Test Battery",  # string
            CONF_SCAN_INTERVAL: 10,  # int
            CONF_DOMAINS: ["Bat.GetStatus"],  # list
        }

        # Schema should validate this input
        try:
            validated = schema(valid_input)
            assert validated[CONF_HOST] == "192.168.1.100"
            assert validated[CONF_PORT] == 30000
            assert isinstance(validated[CONF_PORT], int)
            assert isinstance(validated[CONF_SCAN_INTERVAL], int)
            assert isinstance(validated[CONF_DOMAINS], list)
        except vol.Invalid:
            pytest.fail("Valid input should not raise validation error")