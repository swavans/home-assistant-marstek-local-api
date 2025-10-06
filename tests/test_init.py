"""Tests for the Marstek Local API integration init module."""
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from custom_components.marstek_local_api import (
    DOMAIN,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)


class TestIntegrationSetup:
    """Test integration setup and teardown."""

    @pytest.mark.asyncio
    async def test_async_setup_returns_true(self, hass: HomeAssistant):
        """Test that async_setup returns True."""
        config = {}
        result = await async_setup(hass, config)
        assert result is True

    @pytest.mark.asyncio
    async def test_async_setup_entry_success(self, hass: HomeAssistant, mock_config_entry):
        """Test successful config entry setup."""
        # Ensure hass.data[DOMAIN] exists
        hass.data.setdefault(DOMAIN, {})

        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.return_value = True
            
            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            
            # Check that data was stored
            assert DOMAIN in hass.data
            assert mock_config_entry.entry_id in hass.data[DOMAIN]
            
            stored_data = hass.data[DOMAIN][mock_config_entry.entry_id]
            assert stored_data["host"] == mock_config_entry.data[CONF_HOST]
            assert stored_data["port"] == mock_config_entry.data[CONF_PORT]
            
            # Check that platform setup was called
            mock_forward.assert_called_once_with(mock_config_entry, ["sensor"])

    @pytest.mark.asyncio
    async def test_async_setup_entry_stores_correct_data(self, hass: HomeAssistant):
        """Test that config entry data is stored correctly."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: "10.0.0.50",
                CONF_PORT: 31000,
                "device_name": "Custom Battery",
                "scan_interval": 30,
            },
            entry_id="custom_entry",
        )

        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.return_value = True
            
            result = await async_setup_entry(hass, config_entry)

            assert result is True
            
            stored_data = hass.data[DOMAIN][config_entry.entry_id]
            assert stored_data["host"] == "10.0.0.50"
            assert stored_data["port"] == 31000

    @pytest.mark.asyncio
    async def test_async_setup_entry_multiple_entries(self, hass: HomeAssistant):
        """Test setting up multiple config entries."""
        entry1 = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "192.168.1.100", CONF_PORT: 30000},
            entry_id="entry1",
        )
        entry2 = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "192.168.1.101", CONF_PORT: 30001},
            entry_id="entry2",
        )

        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.return_value = True
            
            result1 = await async_setup_entry(hass, entry1)
            result2 = await async_setup_entry(hass, entry2)

            assert result1 is True
            assert result2 is True
            
            # Both entries should be stored
            assert len(hass.data[DOMAIN]) == 2
            assert "entry1" in hass.data[DOMAIN]
            assert "entry2" in hass.data[DOMAIN]
            
            assert hass.data[DOMAIN]["entry1"]["host"] == "192.168.1.100"
            assert hass.data[DOMAIN]["entry2"]["host"] == "192.168.1.101"

    @pytest.mark.asyncio
    async def test_async_setup_entry_platform_forward_error(self, hass: HomeAssistant, mock_config_entry):
        """Test handling of platform forwarding errors."""
        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.side_effect = Exception("Platform setup failed")
            
            # Should propagate the exception
            with pytest.raises(Exception, match="Platform setup failed"):
                await async_setup_entry(hass, mock_config_entry)

    @pytest.mark.asyncio
    async def test_async_unload_entry_success(self, hass: HomeAssistant, mock_config_entry):
        """Test successful config entry unloading."""
        # First set up the entry
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "host": mock_config_entry.data[CONF_HOST],
            "port": mock_config_entry.data[CONF_PORT],
        }

        with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms") as mock_unload:
            mock_unload.return_value = True
            
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            
            # Check that platform unload was called
            mock_unload.assert_called_once_with(mock_config_entry, ["sensor"])
            
            # Check that data was removed
            assert mock_config_entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_async_unload_entry_platform_unload_failure(self, hass: HomeAssistant, mock_config_entry):
        """Test config entry unloading when platform unload fails."""
        # First set up the entry
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "host": mock_config_entry.data[CONF_HOST],
            "port": mock_config_entry.data[CONF_PORT],
        }

        with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms") as mock_unload:
            mock_unload.return_value = False  # Unload failed
            
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is False
            
            # Data should NOT be removed when unload fails
            assert mock_config_entry.entry_id in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_async_unload_entry_missing_data(self, hass: HomeAssistant, mock_config_entry):
        """Test unloading entry when data doesn't exist."""
        # Don't set up any data
        hass.data.setdefault(DOMAIN, {})

        with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms") as mock_unload:
            mock_unload.return_value = True
            
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            
            # Should not raise error even if entry_id doesn't exist

    @pytest.mark.asyncio
    async def test_async_unload_entry_multiple_entries(self, hass: HomeAssistant):
        """Test unloading one entry while others remain."""
        entry1 = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "192.168.1.100", CONF_PORT: 30000},
            entry_id="entry1",
        )
        entry2 = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "192.168.1.101", CONF_PORT: 30001},
            entry_id="entry2",
        )

        # Set up both entries
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["entry1"] = {"host": "192.168.1.100", "port": 30000}
        hass.data[DOMAIN]["entry2"] = {"host": "192.168.1.101", "port": 30001}

        with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms") as mock_unload:
            mock_unload.return_value = True
            
            result = await async_unload_entry(hass, entry1)

            assert result is True
            
            # Only entry1 should be removed
            assert "entry1" not in hass.data[DOMAIN]
            assert "entry2" in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_domain_data_initialization(self, hass: HomeAssistant, mock_config_entry):
        """Test that domain data is properly initialized."""
        # Start with empty hass.data
        if DOMAIN in hass.data:
            del hass.data[DOMAIN]

        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.return_value = True
            
            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            assert DOMAIN in hass.data
            assert isinstance(hass.data[DOMAIN], dict)

    @pytest.mark.asyncio
    async def test_entry_data_persistence(self, hass: HomeAssistant):
        """Test that entry data persists correctly across operations."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: "192.168.1.123",
                CONF_PORT: 32000,
                "extra_field": "extra_value",
            },
            entry_id="persistence_test",
        )

        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.return_value = True
            
            await async_setup_entry(hass, config_entry)

            # Verify only host and port are stored (not extra fields)
            stored_data = hass.data[DOMAIN][config_entry.entry_id]
            assert stored_data["host"] == "192.168.1.123"
            assert stored_data["port"] == 32000
            assert "extra_field" not in stored_data

    @pytest.mark.asyncio
    async def test_platform_list_correct(self, hass: HomeAssistant, mock_config_entry):
        """Test that correct platforms are forwarded."""
        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.return_value = True
            
            await async_setup_entry(hass, mock_config_entry)

            # Should only forward sensor platform
            mock_forward.assert_called_once_with(mock_config_entry, ["sensor"])

        with patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms") as mock_unload:
            mock_unload.return_value = True
            
            await async_unload_entry(hass, mock_config_entry)

            # Should unload the same sensor platform
            mock_unload.assert_called_once_with(mock_config_entry, ["sensor"])