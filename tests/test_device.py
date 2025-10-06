"""Tests for MarstekDevice class."""
import pytest
import socket
import json
import time
import sys
import os
from unittest.mock import Mock, patch, call
from datetime import timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from custom_components.marstek_local_api.sensor import MarstekDevice


class TestMarstekDevice:
    """Test MarstekDevice UDP communication and caching."""

    def test_device_initialization(self):
        """Test device is properly initialized."""
        host = "192.168.1.100"
        port = 30000
        methods = ["Bat.GetStatus", "Wifi.GetStatus"]
        scan_interval = 10
        device_name = "Test Battery"

        device = MarstekDevice(host, port, methods, scan_interval, device_name)

        assert device._host == host
        assert device._port == port
        assert device._methods == methods
        assert device._device_name == device_name
        assert device._cache == {}

    @patch("socket.socket")
    @patch("time.sleep")
    def test_update_successful_communication(self, mock_sleep, mock_socket_class, mock_json_response, mock_device_data):
        """Test successful UDP communication and caching."""
        # Setup mock socket
        mock_sock = Mock()
        mock_socket_class.return_value = mock_sock
        
        # Mock successful receives for each method
        responses = []
        methods = ["Bat.GetStatus", "Wifi.GetStatus"]
        for method in methods:
            data = mock_device_data[method]
            response = mock_json_response(method, data)
            responses.append((json.dumps(response).encode(), ("192.168.1.100", 30000)))
        
        mock_sock.recvfrom.side_effect = responses

        # Create device and update
        device = MarstekDevice("192.168.1.100", 30000, methods, 10, "Test Battery")
        device.update()

        # Verify socket operations
        mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
        mock_sock.settimeout.assert_called_once_with(2.0)
        mock_sock.bind.assert_called_once_with(("0.0.0.0", 30000))
        
        # Verify UDP requests were sent
        assert mock_sock.sendto.call_count == len(methods)
        for i, method in enumerate(methods):
            expected_payload = {"id": method, "method": method, "params": {"id": 0}}
            call_args = mock_sock.sendto.call_args_list[i]
            sent_data = call_args[0][0]
            sent_address = call_args[0][1]
            
            assert json.loads(sent_data.decode()) == expected_payload
            assert sent_address == ("192.168.1.100", 30000)

        # Verify data was cached
        assert device._cache["Bat.GetStatus"]["soc"] == 85
        assert device._cache["Wifi.GetStatus"]["ssid"] == "TestNetwork"
        
        # Verify sleep was called between requests
        assert mock_sleep.call_count == len(methods)
        for call in mock_sleep.call_args_list:
            assert call == call(0.5)

        mock_sock.close.assert_called_once()

    @patch("socket.socket")
    @patch("time.sleep")
    def test_update_with_socket_timeout(self, mock_sleep, mock_socket_class):
        """Test handling of socket timeouts during communication."""
        mock_sock = Mock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recvfrom.side_effect = socket.timeout("Timeout")

        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        device.update()

        # Verify empty cache is created for methods with no response
        assert device._cache["Bat.GetStatus"] == {}
        mock_sock.close.assert_called_once()

    @patch("socket.socket")
    @patch("time.sleep")
    def test_update_with_socket_error(self, mock_sleep, mock_socket_class, caplog):
        """Test handling of socket errors during setup."""
        mock_socket_class.side_effect = OSError("Socket error")

        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        
        with caplog.at_level("ERROR"):
            device.update()

        assert "Socket setup failed" in caplog.text
        assert device._cache == {}

    @patch("socket.socket")
    @patch("time.sleep")
    def test_update_with_send_error(self, mock_sleep, mock_socket_class, caplog):
        """Test handling of errors during UDP send operations."""
        mock_sock = Mock()
        mock_socket_class.return_value = mock_sock
        mock_sock.sendto.side_effect = OSError("Send error")

        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        
        with caplog.at_level("ERROR"):
            device.update()

        assert "Error sending request" in caplog.text
        # Should still create empty cache
        assert device._cache["Bat.GetStatus"] == {}
        mock_sock.close.assert_called_once()

    @patch("socket.socket")
    @patch("time.sleep")
    def test_update_with_invalid_json_response(self, mock_sleep, mock_socket_class, caplog):
        """Test handling of invalid JSON responses."""
        mock_sock = Mock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recvfrom.return_value = (b"invalid json", ("192.168.1.100", 30000))

        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        device.update()

        # Should still create empty cache for methods
        assert device._cache["Bat.GetStatus"] == {}
        mock_sock.close.assert_called_once()

    @patch("socket.socket")
    @patch("time.sleep")
    def test_update_with_malformed_response(self, mock_sleep, mock_socket_class):
        """Test handling of responses with missing fields."""
        mock_sock = Mock()
        mock_socket_class.return_value = mock_sock
        
        # Response missing 'result' field
        malformed_response = {"id": "Bat.GetStatus"}
        mock_sock.recvfrom.return_value = (
            json.dumps(malformed_response).encode(),
            ("192.168.1.100", 30000)
        )

        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        device.update()

        # Should cache empty dict as result defaults to {}
        assert device._cache["Bat.GetStatus"] == {}

    def test_get_value_existing_key(self):
        """Test getting existing values from cache."""
        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        device._cache = {
            "Bat.GetStatus": {"soc": 85, "bat_temp": 250}
        }

        assert device.get_value("Bat.GetStatus", "soc") == 85
        assert device.get_value("Bat.GetStatus", "bat_temp") == 250

    def test_get_value_missing_method(self):
        """Test getting value from non-existing method."""
        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        device._cache = {"Bat.GetStatus": {"soc": 85}}

        assert device.get_value("NonExistent.Method", "soc") is None

    def test_get_value_missing_key(self):
        """Test getting non-existing key from existing method."""
        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        device._cache = {"Bat.GetStatus": {"soc": 85}}

        assert device.get_value("Bat.GetStatus", "nonexistent_key") is None

    def test_get_value_empty_cache(self):
        """Test getting value when cache is empty."""
        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")

        assert device.get_value("Bat.GetStatus", "soc") is None

    @patch("socket.socket")
    @patch("time.sleep")
    def test_update_multiple_methods_mixed_success(self, mock_sleep, mock_socket_class, mock_json_response, mock_device_data):
        """Test update with some methods succeeding and others failing."""
        mock_sock = Mock()
        mock_socket_class.return_value = mock_sock
        
        # First method succeeds, second times out
        responses = [
            (json.dumps(mock_json_response("Bat.GetStatus", mock_device_data["Bat.GetStatus"])).encode(), 
             ("192.168.1.100", 30000)),
            socket.timeout("Timeout for second method")
        ]
        mock_sock.recvfrom.side_effect = responses

        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus", "Wifi.GetStatus"], 10, "Test Battery")
        device.update()

        # First method should have data, second should be empty
        assert device._cache["Bat.GetStatus"]["soc"] == 85
        assert device._cache["Wifi.GetStatus"] == {}

    @patch("socket.socket")
    def test_socket_cleanup_on_exception(self, mock_socket_class):
        """Test that socket is properly closed even when exceptions occur."""
        mock_sock = Mock()
        mock_socket_class.return_value = mock_sock
        mock_sock.bind.side_effect = OSError("Bind failed")

        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 10, "Test Battery")
        device.update()

        # Socket should still be closed despite the exception
        mock_sock.close.assert_called_once()

    @patch("custom_components.marstek_local_api.sensor.Throttle")
    def test_throttle_decorator_applied(self, mock_throttle):
        """Test that throttle decorator is properly applied to update method."""
        # Make the mock return a function that just returns the original function
        mock_throttle.return_value = lambda func: func
        
        device = MarstekDevice("192.168.1.100", 30000, ["Bat.GetStatus"], 30, "Test Battery")
        
        # Verify throttle was called with correct timedelta
        mock_throttle.assert_called_once_with(timedelta(seconds=30))