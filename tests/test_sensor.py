"""Tests for MarstekBaseSensor and sensor setup."""
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.helpers.entity import DeviceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from custom_components.marstek_local_api.const import (
    CONF_DEVICE_NAME,
    CONF_DOMAINS,
    DOMAIN,
    OPTIONS,
)
from custom_components.marstek_local_api.sensor import (
    MarstekBaseSensor,
    MarstekDevice,
    async_setup_entry,
)


class TestMarstekBaseSensor:
    """Test MarstekBaseSensor entity."""

    def test_sensor_initialization(self, mock_device):
        """Test sensor is properly initialized."""
        sensor = MarstekBaseSensor(
            device=mock_device,
            method="Bat.GetStatus",
            key="soc",
            name="Battery SOC",
            unit="%",
            transform=None
        )

        assert sensor._device == mock_device
        assert sensor._method == "Bat.GetStatus"
        assert sensor._key == "soc"
        assert sensor._unit == "%"
        assert sensor._state is None
        assert sensor._transform is None
        assert sensor._attr_unique_id == "marstek_local_test_marstek_battery_bat.getstatus_soc"

    def test_sensor_initialization_with_transform(self, mock_device):
        """Test sensor initialization with transform function."""
        transform_func = lambda x: x / 10
        
        sensor = MarstekBaseSensor(
            device=mock_device,
            method="Bat.GetStatus",
            key="bat_temp",
            name="Battery Temperature",
            unit="°C",
            transform=transform_func
        )

        assert sensor._transform == transform_func

    def test_native_value_property(self, mock_device):
        """Test native_value property returns current state."""
        sensor = MarstekBaseSensor(mock_device, "Bat.GetStatus", "soc", "Battery SOC")
        sensor._state = 85

        assert sensor.native_value == 85

    def test_native_unit_of_measurement_property(self, mock_device):
        """Test native_unit_of_measurement property."""
        sensor = MarstekBaseSensor(mock_device, "Bat.GetStatus", "soc", "Battery SOC", unit="%")

        assert sensor.native_unit_of_measurement == "%"

    def test_native_unit_of_measurement_none(self, mock_device):
        """Test native_unit_of_measurement when no unit is provided."""
        sensor = MarstekBaseSensor(mock_device, "Bat.GetStatus", "ssid", "WiFi SSID")

        assert sensor.native_unit_of_measurement is None

    def test_device_info_property(self, mock_device):
        """Test device_info property returns correct DeviceInfo."""
        sensor = MarstekBaseSensor(mock_device, "Bat.GetStatus", "soc", "Battery SOC")

        device_info = sensor._attr_device_info
        # DeviceInfo is a TypedDict, so check its contents instead of type
        assert "identifiers" in device_info
        assert "name" in device_info
        assert "manufacturer" in device_info
        assert device_info["identifiers"] == {(DOMAIN, "192.168.1.100_Bat.GetStatus")}
        assert device_info["name"] == "Battery status"  # From OPTIONS
        assert device_info["manufacturer"] == "Marstek"

    def test_update_successful(self, mock_device):
        """Test successful sensor update."""
        mock_device.get_value.return_value = 85
        sensor = MarstekBaseSensor(mock_device, "Bat.GetStatus", "soc", "Battery SOC")

        sensor.update()

        mock_device.update.assert_called_once()
        mock_device.get_value.assert_called_once_with("Bat.GetStatus", "soc")
        assert sensor._state == 85

    def test_update_with_transform(self, mock_device):
        """Test sensor update with transform function."""
        mock_device.get_value.return_value = 250  # Raw temperature value
        transform_func = lambda x: x / 10  # Convert to actual temperature
        
        sensor = MarstekBaseSensor(
            mock_device, "Bat.GetStatus", "bat_temp", "Battery Temperature", 
            unit="°C", transform=transform_func
        )

        sensor.update()

        assert sensor._state == 25.0  # Transformed value

    def test_update_with_transform_error(self, caplog):
        """Test sensor update when transform function raises exception."""
        # Create a specific mock device for this test
        mock_device = Mock(spec=MarstekDevice)
        mock_device._device_name = "Test Marstek Battery"
        mock_device._host = "192.168.1.100"
        mock_device.get_value = Mock(return_value="invalid")
        mock_device.update = Mock()
        
        transform_func = lambda x: x / 10  # Will fail with string input
        
        sensor = MarstekBaseSensor(
            mock_device, "Bat.GetStatus", "bat_temp", "Battery Temperature",
            transform=transform_func
        )
        sensor._state = 20.0  # Previous state

        with caplog.at_level("ERROR"):
            sensor.update()

        assert "Transform failed" in caplog.text
        assert sensor._state == "invalid"  # Should store the raw value when transform fails

    def test_update_no_value_available(self, caplog):
        """Test sensor update when no value is available from device."""
        # Create a specific mock device for this test
        mock_device = Mock(spec=MarstekDevice)
        mock_device._device_name = "Test Marstek Battery"
        mock_device._host = "192.168.1.100"
        mock_device.get_value = Mock(return_value=None)
        mock_device.update = Mock()
        
        sensor = MarstekBaseSensor(mock_device, "Bat.GetStatus", "soc", "Battery SOC")
        sensor._state = 80  # Previous state

        with caplog.at_level("DEBUG"):
            sensor.update()

        assert sensor._state == 80  # Should keep previous state
        assert "has no new value" in caplog.text

    def test_update_first_time_no_value(self):
        """Test sensor update when no value is available and no previous state."""
        # Create a specific mock device for this test
        mock_device = Mock(spec=MarstekDevice)
        mock_device._device_name = "Test Marstek Battery"
        mock_device._host = "192.168.1.100"
        mock_device.get_value = Mock(return_value=None)
        mock_device.update = Mock()
        
        sensor = MarstekBaseSensor(mock_device, "Bat.GetStatus", "soc", "Battery SOC")

        sensor.update()

        assert sensor._state is None

    def test_boolean_transform(self, mock_device):
        """Test boolean transform function."""
        mock_device.get_value.return_value = 1
        transform_func = lambda v: bool(v) if v is not None else False
        
        sensor = MarstekBaseSensor(
            mock_device, "Bat.GetStatus", "charg_flag", "Charging Flag",
            transform=transform_func
        )

        sensor.update()

        assert sensor._state is True

    def test_boolean_transform_zero(self, mock_device):
        """Test boolean transform with zero value."""
        mock_device.get_value.return_value = 0
        transform_func = lambda v: bool(v) if v is not None else False
        
        sensor = MarstekBaseSensor(
            mock_device, "Bat.GetStatus", "dischrg_flag", "Discharging Flag",
            transform=transform_func
        )

        sensor.update()

        assert sensor._state is False

    def test_float_transform(self):
        """Test float transform function."""
        # Create a specific mock device for this test
        mock_device = Mock(spec=MarstekDevice)
        mock_device._device_name = "Test Marstek Battery"
        mock_device._host = "192.168.1.100"
        mock_device.get_value = Mock(return_value="200.5")
        mock_device.update = Mock()
        
        transform_func = lambda v: float(v)

        sensor = MarstekBaseSensor(
            mock_device, "ES.GetMode", "ongrid_power", "On Grid Power",
            unit="W", transform=transform_func
        )

        sensor.update()

        assert sensor._state == 200.5
        assert isinstance(sensor._state, float)


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_basic(self, hass, mock_config_entry):
        """Test basic sensor setup from config entry."""
        mock_add_entities = AsyncMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Verify entities were added
        mock_add_entities.assert_called_once()
        call_args = mock_add_entities.call_args
        entities = call_args[0][0]
        update_before_add = call_args[0][1]

        assert len(entities) > 0
        assert update_before_add is True

        # Check that entities were created for configured domains
        configured_domains = mock_config_entry.data[CONF_DOMAINS]
        entity_methods = {entity._method for entity in entities}
        
        # Should only have entities for configured domains
        for method in entity_methods:
            assert method in configured_domains

    @pytest.mark.asyncio
    async def test_async_setup_entry_all_domains(self, hass):
        """Test sensor setup with all available domains."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.1.100",
                "port": 30000,
                "device_name": "Test Battery",
                "scan_interval": 10,
                "domains": list(OPTIONS.keys()),  # All domains
            },
        )
        mock_add_entities = AsyncMock()

        await async_setup_entry(hass, config_entry, mock_add_entities)

        entities = mock_add_entities.call_args[0][0]
        
        # Should have entities for all sensor definitions
        expected_methods = set(OPTIONS.keys())
        entity_methods = {entity._method for entity in entities}
        
        for method in expected_methods:
            assert method in entity_methods

    @pytest.mark.asyncio
    async def test_async_setup_entry_specific_sensors(self, hass):
        """Test that specific sensor types are created correctly."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.1.100",
                "port": 30000,
                "device_name": "Test Battery",
                "scan_interval": 10,
                "domains": ["Bat.GetStatus", "Wifi.GetStatus"],
            },
        )
        mock_add_entities = AsyncMock()

        await async_setup_entry(hass, config_entry, mock_add_entities)

        entities = mock_add_entities.call_args[0][0]
        
        # Find specific sensors
        soc_sensors = [e for e in entities if e._key == "soc" and e._method == "Bat.GetStatus"]
        wifi_sensors = [e for e in entities if e._method == "Wifi.GetStatus"]
        pv_sensors = [e for e in entities if e._method == "PV.GetStatus"]
        
        assert len(soc_sensors) == 1
        assert len(wifi_sensors) > 0  # Should have multiple WiFi sensors
        assert len(pv_sensors) == 0  # PV not in configured domains

        # Check SOC sensor properties
        soc_sensor = soc_sensors[0]
        assert soc_sensor._unit == "%"
        assert soc_sensor._transform is None

    @pytest.mark.asyncio
    async def test_async_setup_entry_with_transforms(self, hass):
        """Test that sensors with transform functions are created correctly."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.1.100",
                "port": 30000,
                "device_name": "Test Battery",
                "scan_interval": 10,
                "domains": ["Bat.GetStatus", "ES.GetMode"],
            },
        )
        mock_add_entities = AsyncMock()

        await async_setup_entry(hass, config_entry, mock_add_entities)

        entities = mock_add_entities.call_args[0][0]
        
        # Find sensors with transforms
        charg_flag_sensors = [e for e in entities if e._key == "charg_flag"]
        ongrid_power_sensors = [e for e in entities if e._key == "ongrid_power" and e._method == "ES.GetMode"]
        offgrid_power_sensors = [e for e in entities if e._key == "offgrid_power" and e._method == "ES.GetMode"]
        
        assert len(charg_flag_sensors) == 1
        assert len(ongrid_power_sensors) == 1
        assert len(offgrid_power_sensors) == 1

        # Check that transforms are assigned
        assert charg_flag_sensors[0]._transform is not None
        assert ongrid_power_sensors[0]._transform is not None
        assert offgrid_power_sensors[0]._transform is not None

    @pytest.mark.asyncio
    async def test_async_setup_entry_empty_domains(self, hass):
        """Test sensor setup with empty domains list."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.1.100",
                "port": 30000,
                "device_name": "Test Battery",
                "scan_interval": 30,
                "domains": [],
            },
        )
        mock_add_entities = AsyncMock()

        await async_setup_entry(hass, config_entry, mock_add_entities)

        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_async_setup_entry_missing_scan_interval(self, hass):
        """Test sensor setup when scan_interval is missing from config."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.1.100",
                "port": 30000,
                "device_name": "Test Battery",
                "domains": ["Bat.GetStatus"],
                # scan_interval missing
            },
        )
        mock_add_entities = AsyncMock()

        await async_setup_entry(hass, config_entry, mock_add_entities)

        # Should still work, scan_interval will be None
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) > 0