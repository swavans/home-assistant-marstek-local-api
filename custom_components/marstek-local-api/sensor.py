import socket
import json
import logging
import time
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import Throttle
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL

from .const import DOMAIN, CONF_DOMAINS, OPTIONS, CONF_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)


class MarstekDevice:
    """Manages UDP communication and caches results per method."""

    def __init__(self, host, port, methods, scan_interval, device_name="Marstek Battery"):
        self._host = host
        self._port = port
        self._methods = methods
        self._device_name = device_name
        self._cache = {}
        # Handle None scan_interval by using a default of 10 seconds
        scan_interval = scan_interval or 30
        self.update = Throttle(timedelta(seconds=scan_interval))(self.update)

    def update(self):
        _LOGGER.debug("MarstekDevice: Starting update cycle")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            sock.bind(("0.0.0.0", self._port))  # ephemeral port

            for method in self._methods:
                try:
                    _LOGGER.debug("MarstekDevice: Sending request for %s", method)
                    payload = {"id": method, "method": method, "params": {"id": 0}}
                    sock.sendto(
                        json.dumps(payload, separators=(",", ":")).encode("ascii"),
                        (self._host, self._port),
                    )

                    # Attempt to receive response (non-blocking)
                    try:
                        data, addr = sock.recvfrom(8192)
                        result = json.loads(data.decode())
                        _LOGGER.debug("MARSTEK RECEIVE RAW", result)
                        res_method = result.get("id")
                        res_values = result.get("result", {})
                        if res_method:
                            self._cache[res_method] = res_values
                            _LOGGER.debug(
                                "MarstekDevice: Received data for %s: %s",
                                res_method,
                                res_values,
                            )
                    except socket.timeout:
                        _LOGGER.debug(
                            "MarstekDevice: No response yet for %s", method
                        )

                except Exception as e:
                    _LOGGER.error(
                        "MarstekDevice: Error sending request for %s: %s", method, e
                    )
                finally:
                    time.sleep(0.5)

            # Ensure all methods have at least empty cache
            for method in self._methods:
                if method not in self._cache:
                    self._cache[method] = {}

        except Exception as e:
            _LOGGER.error("MarstekDevice: Socket setup failed: %s", e)
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def get_value(self, method, key):
        return self._cache.get(method, {}).get(key)


class MarstekBaseSensor(SensorEntity):
    """Individual sensor reading values from a shared MarstekDevice."""

    def __init__(self, device: MarstekDevice, method, key, name, unit=None, transform=None):
        self._device = device
        self._method = method
        self._key = key
        self._attr_name = f"{name}"
        self._attr_unique_id = f"marstek_local_{device._device_name.replace(' ', '_').lower()}_{method.lower()}_{key}"
        self._unit = unit
        self._state = None
        self._transform = transform

        domain_name = method
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{device._host}_{domain_name}")},
            name=f"{OPTIONS.get(domain_name, domain_name)}",
            manufacturer="Marstek",
        )

    @property
    def native_value(self):
        return self._state

    @property
    def native_unit_of_measurement(self):
        return self._unit

    def update(self):
        self._device.update()
        value = self._device.get_value(self._method, self._key)
        if value is not None:
            if self._transform:
                try:
                    value = self._transform(value)
                except Exception as e:
                    _LOGGER.error("Transform failed for %s: %s", self._attr_name, e)
            self._state = value
            _LOGGER.debug("Sensor %s updated to %s", self._attr_name, self._state)
        else:
            _LOGGER.debug(
                "Sensor %s has no new value, keeping previous state %s",
                self._attr_name,
                self._state,
            )


async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL)
    device_name = entry.data.get(CONF_DEVICE_NAME, "Marstek Battery")
    
    chosen_domains = entry.data.get(CONF_DOMAINS, list(OPTIONS.keys()))
    device = MarstekDevice(host, port, chosen_domains, scan_interval, device_name)

    sensors_def = [
        # Wifi
        ("Wifi.GetStatus", "ssid", "WiFi SSID", None, None),
        ("Wifi.GetStatus", "rssi", "WiFi RSSI", "dBm", None),
        ("Wifi.GetStatus", "sta_ip", "WiFi IP", None, None),
        ("Wifi.GetStatus", "sta_gate", "WiFi Gateway", None, None),
        ("Wifi.GetStatus", "sta_mask", "WiFi Subnet", None, None),
        ("Wifi.GetStatus", "sta_dns", "WiFi DNS", None, None),

        # Battery
        ("Bat.GetStatus", "soc", "Battery SOC", "%", None),
        ("Bat.GetStatus", "bat_temp", "Battery Temp", "°C",
            lambda v: v / 10 if isinstance(v, (int, float)) else v),
        ("Bat.GetStatus", "bat_capacity", "Battery Capacity", "Wh",
            lambda v: v * 10 if isinstance(v, (int, float)) else v),
        ("Bat.GetStatus", "rated_capacity", "Battery Rated Capacity", "Wh", None),
        ("Bat.GetStatus", "charg_flag", "Battery Charging Flag", None, lambda v: bool(v) if v is not None else False),
        ("Bat.GetStatus", "dischrg_flag", "Battery Discharging Flag", None, lambda v: bool(v) if v is not None else False),


        # PV
        ("PV.GetStatus", "pv_power", "PV Power", "W", None),
        ("PV.GetStatus", "pv_voltage", "PV Voltage", "V", None),
        ("PV.GetStatus", "pv_current", "PV Current", "A", None),

        # ES
        ("ES.GetStatus", "bat_soc", "ES Battery SOC", "%", None),
        ("ES.GetStatus", "bat_cap", "ES Battery Capacity", "Wh", None),
        ("ES.GetStatus", "pv_power", "ES PV Power", "W", None),
        ("ES.GetStatus", "ongrid_power", "ES On-Grid Power", "W", None),
        ("ES.GetStatus", "offgrid_power", "ES Off-Grid Power", "W", None),
        ("ES.GetStatus", "bat_power", "ES Battery Power", "W", None),
        ("ES.GetStatus", "total_pv_energy", "ES Total PV Energy", "Wh", None),
        ("ES.GetStatus", "total_grid_output_energy", "ES Grid Output Energy", "Wh", None),
        ("ES.GetStatus", "total_grid_input_energy", "ES Grid Input Energy", "Wh", None),
        ("ES.GetStatus", "total_load_energy", "ES Total Load Energy", "Wh", None),

        # BLE
        ("BLE.GetStatus", "state", "BLE State", None, None),
        ("BLE.GetStatus", "ble_mac", "BLE MAC", None, None),

        # Charging Status
        ( "ES.GetMode", "mode", "Charging mode", None, None),
        ( "ES.GetMode", "ongrid_power", "Ongrid power", "W", lambda v: float(v)),
        ( "ES.GetMode", "offgrid_power", "Offgrid power (backup power)", "W", lambda v: float(v)),
        ( "ES.GetMode", "bat_soc", "Battery %", "%", None),
    ]

    entities = [
        MarstekBaseSensor(device, *params[:4],transform=params[4])
        for params in sensors_def
        if params[0] in chosen_domains
    ]

    async_add_entities(entities, True)
