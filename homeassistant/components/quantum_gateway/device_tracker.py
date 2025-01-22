"""Support for Verizon FiOS Quantum Gateways."""

from __future__ import annotations

from datetime import timedelta

import voluptuous as vol

from homeassistant.components.device_tracker import (
    CONF_CONSIDER_HOME,
    DOMAIN as DEVICE_TRACKER_DOMAIN,
    PLATFORM_SCHEMA as DEVICE_TRACKER_PLATFORM_SCHEMA,
    ScannerEntity,
    SourceType,
)
from homeassistant.components.device_tracker.const import CONF_NEW_DEVICE_DEFAULTS
from homeassistant.components.device_tracker.legacy import remove_device_from_config
from homeassistant.components.frontend import ConfigType
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PLATFORM, CONF_SSL
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.json import json_dumps
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    _LOGGER,
    CONF_LEGACY_DEVICES_BY_MAC,
    DATA_COODINATOR,
    DEFAULT_HOST,
    DOMAIN,
)
from .coordinator import QuantumGatewayCoordinator

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_SSL, default=True): cv.boolean,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Quantum Gateway device tracker."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COODINATOR]

    legacy_devices_by_mac = entry.data.get(CONF_LEGACY_DEVICES_BY_MAC, {})

    entities = [
        QuantumGatewayScannerEntity(
            coordinator, mac, legacy_devices_by_mac.get(mac, {}).get("dev_id")
        )
        for mac in coordinator.data
    ]

    if entry.source == SOURCE_IMPORT:
        for entity in entities:
            legacy_device = legacy_devices_by_mac.pop(entity.mac_address, None)
            if (
                legacy_device is not None
                and (entity_id := f"{DEVICE_TRACKER_DOMAIN}.{legacy_device['dev_id']}")
                and hass.states.get(entity_id) is not None
            ):
                _LOGGER.debug(
                    "Starting migration for device %s with data %s ",
                    entity_id,
                    json_dumps(legacy_device),
                )
                if hass.states.async_remove(entity_id):
                    remove_device_from_config(hass, legacy_device["dev_id"])
                    _LOGGER.debug("Finished migration for device %s ", entity_id)

                else:
                    _LOGGER.warning(
                        "Failed to remove device %s during migration", entity_id
                    )
                    legacy_devices_by_mac[entity.mac_address] = legacy_device

    async_add_entities(entities)

    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_LEGACY_DEVICES_BY_MAC: legacy_devices_by_mac}
    )


class QuantumGatewayScannerEntity(
    CoordinatorEntity[QuantumGatewayCoordinator], ScannerEntity
):
    """Representation of a Quantum Gateway network device."""

    _attr_mac_address: str

    def __init__(
        self, coordinator: QuantumGatewayCoordinator, mac: str, unique_id: str | None
    ) -> None:
        """Initialize the Quantum Gateway device."""
        super().__init__(coordinator)
        if unique_id is not None:
            self._attr_unique_id = unique_id
        self._attr_source_type = SourceType.ROUTER
        self._attr_mac_address = mac
        self._attr_hostname = self.coordinator.data.get(mac)
        self._is_connected = self.coordinator.data.get(mac) is not None

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        return self._is_connected

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return self.hostname or self.mac_address

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_hostname = self.coordinator.data.get(self._attr_mac_address)
        self._is_connected = (
            self.coordinator.data.get(self._attr_mac_address) is not None
        )
        self.async_write_ha_state()


async def async_get_scanner(hass: HomeAssistant, config: ConfigType) -> None:
    """Legacy init: import through config flow."""
    data = config[DEVICE_TRACKER_DOMAIN]
    data.pop(CONF_PLATFORM, None)
    data.pop(CONF_NEW_DEVICE_DEFAULTS, None)

    if CONF_CONSIDER_HOME in data and isinstance(data[CONF_CONSIDER_HOME], timedelta):
        data[CONF_CONSIDER_HOME] = data[CONF_CONSIDER_HOME].total_seconds()

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=data,
        )
    )

    _LOGGER.warning(
        f"Your {DOMAIN} configuration has been imported into the UI, "
        "please remove it from configuration.yaml. "
        f"Loading {DOMAIN} via platform setup is now deprecated."
    )

    async_create_issue(
        hass,
        HOMEASSISTANT_DOMAIN,
        f"deprecated_yaml_{DOMAIN}",
        breaks_in_ha_version="2026.2.0",
        is_fixable=False,
        issue_domain=DOMAIN,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
        translation_placeholders={
            "domain": DOMAIN,
            "integration_title": "Quantum Gateway",
        },
    )

    return None  # noqa: PLR1711, RET501
