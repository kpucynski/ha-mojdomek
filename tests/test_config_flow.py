"""Tests for the mojdomek.eu config flow."""

from unittest.mock import AsyncMock

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.mojdomek.api import MojdomekError, MojdomekInvalidAccountError
from custom_components.mojdomek.const import CONF_ACCOUNT_ID, DOMAIN
from tests.conftest import make_device

USER_INPUT = {CONF_ACCOUNT_ID: "ACCT0001"}


async def test_user_flow(hass: HomeAssistant, mock_mojdomek: AsyncMock) -> None:
    """Test a successful user flow that selects a device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: "DEV00001"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Septic tank"
    assert result["data"] == {
        CONF_ACCOUNT_ID: "ACCT0001",
        CONF_DEVICE_ID: "DEV00001",
    }
    assert result["result"].unique_id == "DEV00001"


@pytest.mark.parametrize(
    ("side_effect", "return_value", "error"),
    [
        (MojdomekInvalidAccountError("bad"), None, "invalid_auth"),
        (MojdomekError("timeout"), None, "cannot_connect"),
        (RuntimeError("boom"), None, "unknown"),
        (None, {}, "no_devices"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_mojdomek: AsyncMock,
    side_effect: Exception | None,
    return_value: dict | None,
    error: str,
) -> None:
    """Test errors shown by the account step, and recovery afterwards."""
    mock_mojdomek.async_get_devices.side_effect = side_effect
    mock_mojdomek.async_get_devices.return_value = return_value
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_mojdomek.async_get_devices.side_effect = None
    mock_mojdomek.async_get_devices.return_value = {
        "DEV00001": make_device("DEV00001", "Septic tank")
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: "DEV00001"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_no_new_devices(
    hass: HomeAssistant, mock_mojdomek: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test abort when every device of the account is already configured."""
    mock_config_entry.add_to_hass(hass)
    mock_mojdomek.async_get_devices.return_value = {
        "DEV00001": make_device("DEV00001", "Septic tank")
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_new_devices"


async def test_strips_account_id(hass: HomeAssistant, mock_mojdomek: AsyncMock) -> None:
    """Test that surrounding whitespace is stripped from the account ID."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ACCOUNT_ID: "  ACCT0001  "}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: "DEV00001"}
    )
    assert result["data"][CONF_ACCOUNT_ID] == "ACCT0001"
