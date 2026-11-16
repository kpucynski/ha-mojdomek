"""Tests for the mojdomek.eu API client."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from aiohttp import ClientError
import pytest

from custom_components.mojdomek.api import (
    Mojdomek,
    MojdomekError,
    MojdomekInvalidAccountError,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _session(payload: object, *, status: int = 200) -> MagicMock:
    response = AsyncMock()
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value=payload)
    response.__aenter__.return_value = response
    response.__aexit__.return_value = None
    if status >= 400:
        response.raise_for_status.side_effect = ClientError(f"HTTP {status}")

    session = MagicMock()
    session.get = MagicMock(return_value=response)
    return session


async def test_get_devices() -> None:
    """Test parsing a successful account response."""
    payload = json.loads((FIXTURES / "account.json").read_text(encoding="utf-8"))
    api = Mojdomek(_session(payload), "ACCT0001")

    devices = await api.async_get_devices()

    assert list(devices) == ["DEV00001", "DEV00002"]
    septic = devices["DEV00001"]
    assert septic.name == "Septic tank"
    assert septic.model == "SZ04-002"
    assert septic.software == "11.0"
    assert septic.fill_level == 53
    assert septic.level == 85
    assert septic.temperature == 5.2
    assert septic.battery_level == 98.9
    assert septic.battery_voltage == 6
    assert septic.signal_strength == 54
    assert septic.max_level == 195
    assert septic.alarm_level == 160
    assert septic.predicted_full is not None
    assert septic.predicted_full.year == 2026
    assert septic.measured_at is not None
    assert septic.measured_at.tzinfo is not None

    rain = devices["DEV00002"]
    assert rain.fill_level == -6
    assert rain.level == -10


async def test_invalid_account() -> None:
    """Test that an unrecognized account ID raises MojdomekInvalidAccountError."""
    api = Mojdomek(
        _session({"errorcode": "745801", "errormessage": "Invalid user ID"}),
        "BAD",
    )
    with pytest.raises(MojdomekInvalidAccountError):
        await api.async_get_devices()


async def test_api_error() -> None:
    """Test that other API error payloads raise MojdomekError."""
    api = Mojdomek(
        _session({"errorcode": "1", "errormessage": "Something broke"}),
        "ACCT0001",
    )
    with pytest.raises(MojdomekError, match="Something broke"):
        await api.async_get_devices()


async def test_http_error() -> None:
    """Test that HTTP failures raise MojdomekError."""
    api = Mojdomek(_session({}, status=500), "ACCT0001")
    with pytest.raises(MojdomekError, match="Request failed"):
        await api.async_get_devices()


async def test_unexpected_payload() -> None:
    """Test that a response without locations raises MojdomekError."""
    api = Mojdomek(_session({"id": "ACCT0001"}), "ACCT0001")
    with pytest.raises(MojdomekError, match="Unexpected response"):
        await api.async_get_devices()
