"""Config flow for the mojdomek.eu integration."""

import logging
from typing import Any, override

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import probatio

from .api import Mojdomek, MojdomekDevice, MojdomekError, MojdomekInvalidAccountError
from .const import CONF_ACCOUNT_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = probatio.Schema({probatio.Required(CONF_ACCOUNT_ID): str})


class MojdomekConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a mojdomek.eu liquid level sensor."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._account_id: str | None = None
        self._devices: dict[str, MojdomekDevice] = {}

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            account_id = user_input[CONF_ACCOUNT_ID].strip()
            api = Mojdomek(async_get_clientsession(self.hass), account_id)
            try:
                devices = await api.async_get_devices()
            except MojdomekInvalidAccountError:
                errors["base"] = "invalid_auth"
            except MojdomekError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    configured = self._async_current_ids()
                    self._devices = {
                        device_id: device
                        for device_id, device in devices.items()
                        if device_id not in configured
                    }
                    if not self._devices:
                        return self.async_abort(reason="no_new_devices")
                    self._account_id = account_id
                    return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick which device of the account to add."""
        if user_input is not None:
            device = self._devices[user_input[CONF_DEVICE_ID]]
            await self.async_set_unique_id(device.id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=device.name,
                data={CONF_ACCOUNT_ID: self._account_id, CONF_DEVICE_ID: device.id},
            )

        return self.async_show_form(
            step_id="device",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_DEVICE_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(
                                    value=device.id,
                                    label=f"{device.name} ({device.id})",
                                )
                                for device in self._devices.values()
                            ],
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )
