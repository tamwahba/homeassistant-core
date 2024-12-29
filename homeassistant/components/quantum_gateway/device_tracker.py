"""Support for Verizon FiOS Quantum Gateways."""

from __future__ import annotations

from requests.exceptions import RequestException
import voluptuous as vol

from homeassistant.components.device_tracker import (
    DOMAIN as DEVICE_TRACKER_DOMAIN,
    PLATFORM_SCHEMA as DEVICE_TRACKER_PLATFORM_SCHEMA,
    DeviceScanner,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import _LOGGER, DATA_COODINATOR, DEFAULT_HOST, DOMAIN
from .coordinator import QuantumGatewayCoordinator

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_SSL, default=True): cv.boolean,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


async def async_get_scanner(
    hass: HomeAssistant, config: ConfigType
) -> QuantumGatewayDeviceScanner | None:
    """Validate the configuration and return a Quantum Gateway scanner."""
    coordinator = hass.data[DOMAIN][config[DEVICE_TRACKER_DOMAIN][CONF_HOST]][
        DATA_COODINATOR
    ]
    if coordinator is None:
        return None

    return QuantumGatewayDeviceScanner(hass, coordinator)


class QuantumGatewayDeviceScanner(DeviceScanner):
    """Class which queries a Quantum Gateway."""

    def __init__(
        self, hass: HomeAssistant, coordinator: QuantumGatewayCoordinator
    ) -> None:
        """Initialize the scanner."""

        _LOGGER.debug("Initializing")

        self.coordinator = coordinator

    async def async_scan_devices(self) -> list[str]:
        """Scan for new devices and return a list of found MACs."""
        connected_devices: list[str] = []
        try:
            await self.coordinator.async_refresh()
            connected_devices = list(self.coordinator.data)
        except RequestException:
            _LOGGER.error("Unable to scan devices. Check connection to router")
        return connected_devices

    def get_device_name(self, device: str) -> str | None:
        """Return the name of the given device or None if we don't know."""
        return self.coordinator.data.get(device)
