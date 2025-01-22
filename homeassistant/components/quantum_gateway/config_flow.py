"""Config flow for Quantum Gateway integration."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.device_tracker import (
    CONF_CONSIDER_HOME,
    DEFAULT_CONSIDER_HOME,
)
from homeassistant.components.device_tracker.legacy import (
    YAML_DEVICES,
    async_load_config,
)
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_SSL
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import format_mac

from .const import (
    CONF_LEGACY_DEVICES_BY_MAC,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL.total_seconds()
        ): cv.positive_int,
        vol.Required(
            CONF_CONSIDER_HOME, default=DEFAULT_CONSIDER_HOME.total_seconds()
        ): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=900)),
        vol.Required(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_SSL, default=True): cv.boolean,
    }
)


class QuantumGatewayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Quantum Gateway config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

        return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import Quantum Gateway config entry from configuration.yaml."""
        try:
            import_data = CONFIG_SCHEMA(import_data)
        except vol.MultipleInvalid as err:
            return self.async_show_form(
                step_id="import",
                data_schema=CONFIG_SCHEMA,
                errors={
                    "base": f"failed to import from yaml: {[e.error_message for e in err.errors]}"
                },
            )

        self._async_abort_entries_match({CONF_HOST: import_data[CONF_HOST]})

        known_devices = await async_load_config(
            self.hass.config.path(YAML_DEVICES),
            self.hass,
            import_data[CONF_CONSIDER_HOME],
        )

        import_data[CONF_LEGACY_DEVICES_BY_MAC] = {
            format_mac(device.mac): {
                "consider_home": device.consider_home.total_seconds(),
                "track": device.track,
                "dev_id": device.dev_id,
                "mac": device.mac,
                "name": device.name,
                "config_picture": device.config_picture,
                "icon": device.icon,
            }
            for device in known_devices
        }

        return self.async_create_entry(title=import_data[CONF_HOST], data=import_data)
