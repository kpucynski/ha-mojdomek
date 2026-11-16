"""Async client for the mojdomek.eu liquid level sensor API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientError, ClientSession, ClientTimeout

API_URL = "https://mojdomek.eu/api/api2.php"

# The API reports timestamps as Polish local time without a UTC offset.
API_TIME_ZONE = ZoneInfo("Europe/Warsaw")

# "Invalid user ID" and "no data", which is returned for a missing or malformed ID.
INVALID_ACCOUNT_ERROR_CODES = {"745801", "90976"}


class MojdomekError(Exception):
    """Raised when the API cannot be reached or returns an unusable response."""


class MojdomekInvalidAccountError(MojdomekError):
    """Raised when the API does not accept the account ID."""


@dataclass(frozen=True, kw_only=True)
class MojdomekDevice:
    """A liquid level sensor and its latest measurement."""

    id: str
    name: str
    model: str | None
    software: str | None
    max_level: float | None
    alarm_level: float | None
    fill_level: float | None
    level: float | None
    temperature: float | None
    battery_level: float | None
    battery_voltage: float | None
    signal_strength: float | None
    predicted_full: datetime | None
    last_emptied: datetime | None
    measured_at: datetime | None


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=API_TIME_ZONE)
    except ValueError:
        return None


def _parse_device(location: dict[str, Any]) -> MojdomekDevice:
    measurement = location.get("measurement") or {}
    return MojdomekDevice(
        id=location["id"],
        name=location.get("name") or location["id"],
        model=location.get("mainboard"),
        software=location.get("software"),
        max_level=location.get("max"),
        alarm_level=location.get("alarm"),
        fill_level=measurement.get("percent"),
        level=measurement.get("cm"),
        temperature=measurement.get("temperature"),
        battery_level=measurement.get("batt_level"),
        battery_voltage=measurement.get("volts"),
        signal_strength=measurement.get("rssi"),
        predicted_full=_timestamp(measurement.get("nextfull")),
        last_emptied=_timestamp(measurement.get("lastempty")),
        measured_at=_timestamp(measurement.get("datatime")),
    )


class Mojdomek:
    """Client for the devices of one mojdomek.eu account."""

    def __init__(
        self, session: ClientSession, account_id: str, timeout: float = 10
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._account_id = account_id
        self._timeout = ClientTimeout(total=timeout)

    async def async_get_devices(self) -> dict[str, MojdomekDevice]:
        """Return every device of the account, keyed by device ID."""
        try:
            async with self._session.get(
                API_URL, params={"id": self._account_id}, timeout=self._timeout
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except (ClientError, TimeoutError, ValueError) as err:
            raise MojdomekError(f"Request failed: {err!r}") from err

        # Errors are reported with HTTP status 200.
        if isinstance(data, dict) and "errormessage" in data:
            if data.get("errorcode") in INVALID_ACCOUNT_ERROR_CODES:
                raise MojdomekInvalidAccountError(data["errormessage"])
            raise MojdomekError(
                f"API error {data.get('errorcode')}: {data['errormessage']}"
            )

        try:
            return {
                location["id"]: _parse_device(location)
                for location in data["locations"]
            }
        except (KeyError, TypeError) as err:
            raise MojdomekError(f"Unexpected response: {err!r}") from err
