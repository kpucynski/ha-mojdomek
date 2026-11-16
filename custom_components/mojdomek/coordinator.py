"""Data update coordinator for the mojdomek.eu integration."""

import datetime as dt
import logging
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Mojdomek, MojdomekDevice, MojdomekError
from .const import CONF_ACCOUNT_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

# The sensors report at most every 15 minutes.
UPDATE_INTERVAL = dt.timedelta(minutes=15)

type MojdomekConfigEntry = ConfigEntry[MojdomekCoordinator]


class MojdomekCoordinator(DataUpdateCoordinator[MojdomekDevice]):
    """Poll the latest measurement of one liquid level sensor."""

    config_entry: MojdomekConfigEntry

    def __init__(self, hass: HomeAssistant, entry: MojdomekConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=UPDATE_INTERVAL,
        )
        self.device_id: str = entry.data[CONF_DEVICE_ID]
        self.api = Mojdomek(async_get_clientsession(hass), entry.data[CONF_ACCOUNT_ID])

    @override
    async def _async_update_data(self) -> MojdomekDevice:
        try:
            devices = await self.api.async_get_devices()
        except MojdomekError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        if (device := devices.get(self.device_id)) is None:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="device_not_found",
                translation_placeholders={"device_id": self.device_id},
            )
        return device
