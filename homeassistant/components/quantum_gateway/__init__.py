"""The quantum_gateway component."""

from requests import RequestException

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.components.frontend import ConfigType
from homeassistant.const import CONF_HOST, CONF_PLATFORM
from homeassistant.core import HomeAssistant

from .const import _LOGGER, DATA_COODINATOR, DOMAIN
from .coordinator import QuantumGatewayCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Quantum Gateway component."""

    options = next(
        conf
        for conf in config.get(DEVICE_TRACKER_DOMAIN, [])
        if conf.get(CONF_PLATFORM) == DOMAIN
    )
    if not options:
        return True

    hass.data.setdefault(DOMAIN, {})
    if options[CONF_HOST] not in hass.data[DOMAIN]:
        hass.data[DOMAIN][options[CONF_HOST]] = {}

    coordinator = QuantumGatewayCoordinator(hass, options)

    try:
        await coordinator.async_config_entry_first_refresh()
        success_init = True
    except RequestException:
        success_init = False
        _LOGGER.error("Unable to connect to gateway. Check host")

    if not success_init:
        _LOGGER.error("Unable to login to gateway. Check password and host")

    hass.data[DOMAIN][options[CONF_HOST]][DATA_COODINATOR] = (
        coordinator if success_init else None
    )

    return success_init
