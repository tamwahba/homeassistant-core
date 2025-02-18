"""Test the Quantum Gateway coordinator."""

from datetime import timedelta
from random import randint
from unittest.mock import patch

from homeassistant.components.device_tracker.const import CONF_CONSIDER_HOME
from homeassistant.components.quantum_gateway.const import DATA_COODINATOR, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_SSL
from homeassistant.core import HomeAssistant

from .util import MockScanner

from tests.common import MockConfigEntry


async def test_sets_update_interval_from_options(hass: HomeAssistant) -> None:
    """Test the update interval is set from the options."""
    scan_interval = randint(1, 60)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: True,
            CONF_CONSIDER_HOME: 180,
            CONF_SCAN_INTERVAL: scan_interval,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.quantum_gateway.coordinator.get_scanner",
        return_value=MockScanner(True),
    ) as get_scanner:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        get_scanner.assert_called_once()

        assert entry.state is ConfigEntryState.LOADED

        coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COODINATOR]

        assert coordinator.update_interval == timedelta(seconds=scan_interval)
