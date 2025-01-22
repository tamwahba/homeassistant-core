"""Coordinator for the Quantum Gateway integration."""

from datetime import timedelta
from types import MappingProxyType
from typing import Any, override

from quantum_gateway import QuantumGatewayScanner

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import _LOGGER


def get_scanner(host: str, password: str, use_https: bool) -> QuantumGatewayScanner:
    """Return a Quantum Gateway scanner."""
    return QuantumGatewayScanner(host, password, use_https)


class QuantumGatewayCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Class to manage fetching data from the Quantum Gateway router."""

    def __init__(
        self, hass: HomeAssistant, options: MappingProxyType[str, Any]
    ) -> None:
        """Initialize the data coordinator."""
        update_interval = options.get(CONF_SCAN_INTERVAL)
        if update_interval is not None:
            update_interval = timedelta(update_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="Quantum Gateway device scanner",
            update_interval=update_interval,
            always_update=False,
        )
        self.options = options
        self._scanner: QuantumGatewayScanner | None = None

    @override
    async def _async_setup(self):
        """Set up the Quantum Gateway device scanner."""
        self._scanner = await self.hass.async_add_executor_job(
            get_scanner,
            self.options[CONF_HOST],
            self.options[CONF_PASSWORD],
            self.options[CONF_SSL],
        )

    @override
    async def _async_update_data(self):
        """Fetch the latest data from the Quantum Gateway."""
        macs = await self.hass.async_add_executor_job(self._scanner.scan_devices)
        return {mac: self._scanner.get_device_name(mac) for mac in macs}
