"""The quantum_gateway component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COODINATOR, DOMAIN, PLATFORMS
from .coordinator import QuantumGatewayCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Quantum Gateway from a config entry."""
    data = entry.data
    coordinator = QuantumGatewayCoordinator(hass, data)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id][DATA_COODINATOR] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
