"""Constants for Quantum Gateway."""

from datetime import timedelta
import logging

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN

_LOGGER = logging.getLogger(__package__)

DOMAIN = "quantum_gateway"

DATA_COODINATOR = "coordinator"

CONF_IMPORTED_BY = "imported_by"
CONF_LEGACY_DEVICES_BY_MAC = "legacy_devices_by_mac"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

PLATFORMS = [DEVICE_TRACKER_DOMAIN]

DEFAULT_HOST = "myfiosgateway.com"
