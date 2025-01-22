"""Test the Quantum Gateway config flow."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

from requests.exceptions import ConnectionError, Timeout

from homeassistant import config_entries
from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.components.quantum_gateway.const import (
    CONF_LEGACY_DEVICES_BY_MAC,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@dataclass
class MockScanner:
    """Mock data class for simulating QuantumGatewayScanner."""

    success_init: bool


async def ensure_error_recovered(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, flow_id: str, additional_data=None
) -> None:
    """Run assertions to ensure the error is recovered."""
    if additional_data is None:
        additional_data = {}

    with patch(
        "homeassistant.components.quantum_gateway.config_flow.get_scanner",
        return_value=MockScanner(True),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_HOST: "1.1.1.1",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "1.1.1.1"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
        CONF_SSL: True,
        CONF_CONSIDER_HOME: 180,
        CONF_SCAN_INTERVAL: 30,
        **additional_data,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.quantum_gateway.config_flow.get_scanner",
        return_value=MockScanner(True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "1.1.1.1"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
        CONF_SSL: True,
        CONF_CONSIDER_HOME: 180,
        CONF_SCAN_INTERVAL: 30,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.quantum_gateway.config_flow.get_scanner",
        return_value=MockScanner(False),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    await ensure_error_recovered(hass, mock_setup_entry, result["flow_id"])


async def test_form_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.quantum_gateway.config_flow.get_scanner",
        side_effect=ConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    await ensure_error_recovered(hass, mock_setup_entry, result["flow_id"])


async def test_form_timeout(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we handle timeout error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.quantum_gateway.config_flow.get_scanner",
        side_effect=Timeout,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    await ensure_error_recovered(hass, mock_setup_entry, result["flow_id"])


async def test_form_other_error(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle any other error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.quantum_gateway.config_flow.get_scanner",
        side_effect=RuntimeError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}

    await ensure_error_recovered(hass, mock_setup_entry, result["flow_id"])


async def test_import(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we can do an import."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_IMPORT,
        },
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "1.1.1.1"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
        CONF_SSL: True,
        CONF_CONSIDER_HOME: 180,
        CONF_SCAN_INTERVAL: 30,
        CONF_LEGACY_DEVICES_BY_MAC: {},
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_validation_error(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we can handle an import validation error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_IMPORT,
        },
        data={
            CONF_HOST: "1.1.1.1",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_yaml"}

    await ensure_error_recovered(
        hass, mock_setup_entry, result["flow_id"], {CONF_LEGACY_DEVICES_BY_MAC: {}}
    )
