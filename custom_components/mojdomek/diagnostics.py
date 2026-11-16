"""Diagnostics support for the mojdomek.eu integration."""

import dataclasses
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_ACCOUNT_ID
from .coordinator import MojdomekConfigEntry

# The account ID is the only credential the API needs.
TO_REDACT = {CONF_ACCOUNT_ID}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: MojdomekConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return {
        "entry_data": async_redact_data(config_entry.data, TO_REDACT),
        "device": dataclasses.asdict(config_entry.runtime_data.data),
    }
