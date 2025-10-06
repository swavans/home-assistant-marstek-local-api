"""Test the entity naming with device name."""
import pytest
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from custom_components.marstek_local_api.sensor import MarstekDevice, MarstekBaseSensor


def test_entity_naming_with_device_name():
    """Test that entity names include the device name."""
    device_name = "My Custom Battery"
    device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, device_name)
    
    sensor = MarstekBaseSensor(
        device=device,
        method="Bat.GetStatus",
        key="soc",
        name="Battery SOC",
        unit="%"
    )
    
    # Test that the sensor name includes the device name
    assert sensor._attr_name == "My Custom Battery Battery SOC"
    
    # Test that the unique_id includes the device name with underscores
    expected_unique_id = "marstek_local_my_custom_battery_bat.getstatus_soc"
    assert sensor._attr_unique_id == expected_unique_id


def test_entity_naming_with_default_device_name():
    """Test that entity names work with default device name."""
    device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10)  # No device name provided
    
    sensor = MarstekBaseSensor(
        device=device,
        method="Bat.GetStatus", 
        key="soc",
        name="Battery SOC",
        unit="%"
    )
    
    # Test with default device name
    assert sensor._attr_name == "Marstek Battery Battery SOC"
    assert sensor._attr_unique_id == "marstek_local_marstek_battery_bat.getstatus_soc"


def test_entity_naming_with_spaces_and_special_chars():
    """Test entity naming handles spaces and special characters."""
    device_name = "Kitchen Battery #1"
    device = MarstekDevice("192.168.1.100", 30000, ["Wifi.GetStatus"], 10, device_name)
    
    sensor = MarstekBaseSensor(
        device=device,
        method="Wifi.GetStatus",
        key="ssid", 
        name="WiFi SSID"
    )
    
    # Test that spaces are converted to underscores in unique_id but preserved in name
    assert sensor._attr_name == "Kitchen Battery #1 WiFi SSID"
    assert sensor._attr_unique_id == "marstek_local_kitchen_battery_#1_wifi.getstatus_ssid"