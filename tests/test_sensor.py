"""Tests for the mojdomek.eu sensor platform."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant.common import MockConfigEntry


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, mock_mojdomek: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Set up the integration with the mocked API client."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.parametrize(
    ("entity_id", "state"),
    [
        ("sensor.septic_tank_fill_level", "53"),
        ("sensor.septic_tank_liquid_level", "85"),
        ("sensor.septic_tank_temperature", "5.2"),
        ("sensor.septic_tank_battery", "98.9"),
        ("sensor.septic_tank_battery_voltage", "6"),
        ("sensor.septic_tank_signal_strength", "54"),
        ("sensor.septic_tank_predicted_full", "2026-11-23T04:33:48+00:00"),
        ("sensor.septic_tank_last_emptied", "2026-11-09T05:36:12+00:00"),
        ("sensor.septic_tank_last_measurement", "2026-11-16T09:18:30+00:00"),
    ],
)
async def test_states(hass: HomeAssistant, entity_id: str, state: str) -> None:
    """Test sensor states for a liquid level sensor."""
    assert (entity := hass.states.get(entity_id))
    assert entity.state == state


@pytest.mark.usefixtures("setup_integration")
async def test_disabled_by_default(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test that configuration sensors are registered but disabled."""
    for entity_id in (
        "sensor.septic_tank_alarm_level",
        "sensor.septic_tank_maximum_level",
    ):
        assert (entry := entity_registry.async_get(entity_id))
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert hass.states.get(entity_id) is None


async def test_disabled_sensor_values(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_mojdomek: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test values of sensors that are disabled by default once enabled."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    for entity_id in (
        "sensor.septic_tank_alarm_level",
        "sensor.septic_tank_maximum_level",
    ):
        entity_registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.septic_tank_alarm_level").state == "160"
    assert hass.states.get("sensor.septic_tank_maximum_level").state == "195"


async def test_missing_device(
    hass: HomeAssistant, mock_mojdomek: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test that setup fails when the configured device is gone from the account."""
    mock_mojdomek.async_get_devices.return_value = {}
    mock_config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.septic_tank_fill_level") is None
