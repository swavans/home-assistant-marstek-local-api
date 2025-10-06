import logging

from homeassistant.const import CONF_HOST, CONF_PORT

DOMAIN = "marstek_local_api"
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    return True


async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "host": entry.data[CONF_HOST],
        "port": entry.data[CONF_PORT],
    }

    # Nieuwere API: meerdere platforms tegelijk
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass, entry):
    # Nieuwere API: netjes ontladen
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
