"""Test utilitites for Quantum Gateway."""

from dataclasses import dataclass, field


@dataclass
class MockScanner:
    """Mock data class for simulating QuantumGatewayScanner."""

    success_init: bool
    devices: dict[str, str] = field(default_factory=dict)

    def scan_devices(self):
        """Scan devices."""
        return self.devices.copy()
