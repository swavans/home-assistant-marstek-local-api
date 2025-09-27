import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from .const import DOMAIN, CONF_DOMAINS, OPTIONS


class MarstekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marstek Battery."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Marstek Battery",
                data=user_input
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=30000): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=10): int,
                vol.Optional(
                    CONF_DOMAINS,
                    default=list(OPTIONS.keys())
                ): cv.multi_select(OPTIONS),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
