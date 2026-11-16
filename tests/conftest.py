"""Fixtures for the mojdomek.eu integration tests."""

from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from homeassistant.const import CONF_DEVICE_ID
import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.mojdomek.api import MojdomekDevice
from custom_components.mojdomek.const import CONF_ACCOUNT_ID, DOMAIN

API_TZ = ZoneInfo("Europe/Warsaw")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""


def make_device(
    device_id: str = "DEV00001",
    name: str = "Septic tank",
    *,
    fill_level: float | None = 53,
    level: float | None = 85,
) -> MojdomekDevice:
    """Return a liquid level sensor with realistic measurements."""
    return MojdomekDevice(
        id=device_id,
        name=name,
        model="SZ04-002",
        software="11.0",
        max_level=195,
        alarm_level=160,
        fill_level=fill_level,
        level=level,
        temperature=5.2,
        battery_level=98.9,
        battery_voltage=6,
        signal_strength=54,
        predicted_full=datetime(2026, 11, 23, 5, 33, 48, tzinfo=API_TZ),
        last_emptied=datetime(2026, 11, 9, 6, 36, 12, tzinfo=API_TZ),
        measured_at=datetime(2026, 11, 16, 10, 18, 30, tzinfo=API_TZ),
    )


@pytest.fixture
def mock_mojdomek() -> Generator[AsyncMock]:
    """Mock the Mojdomek client used by the coordinator and config flow."""
    with (
        patch(
            "custom_components.mojdomek.coordinator.Mojdomek", autospec=True
        ) as client_class,
        patch("custom_components.mojdomek.config_flow.Mojdomek", new=client_class),
    ):
        client = client_class.return_value
        devices = {
            "DEV00001": make_device("DEV00001", "Septic tank"),
            "DEV00002": make_device("DEV00002", "Rain tank", fill_level=-6, level=-10),
        }
        client.async_get_devices.return_value = devices
        yield client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry for one liquid level sensor."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Septic tank",
        unique_id="DEV00001",
        data={CONF_ACCOUNT_ID: "ACCT0001", CONF_DEVICE_ID: "DEV00001"},
    )
