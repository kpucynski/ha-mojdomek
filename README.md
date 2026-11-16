# mojdomek.eu liquid level sensor for Home Assistant

Home Assistant integration for [mojdomek.eu](https://mojdomek.eu) ultrasonic liquid level sensors (cesspits, septic tanks, rainwater tanks, and similar). The cloud API is polled and each selected device is exposed as a Home Assistant device with sensors for fill level, liquid height, temperature, battery, signal, and predicted full / last emptied times.

## Features

- Config flow: enter your mojdomek.eu **account ID**, then pick a device from the account.
- One Home Assistant device per sensor, with:
  - fill level (%)
  - liquid level (cm)
  - temperature
  - predicted full and last emptied timestamps
  - battery level and voltage, signal strength, and last measurement (diagnostic)
  - alarm and maximum level (diagnostic, disabled by default)
- Diagnostics download (account ID redacted).

The API is polled every 15 minutes (sensors typically report at most that often).

## Requirements

- Home Assistant 2026.11.0 or newer.
- A mojdomek.eu account and at least one liquid level sensor linked to it.

## Installation

### HACS

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kpucynski&repository=ha-mojdomek&category=integration)

1. In HACS, open the menu in the top right and select **Custom repositories**.
2. Add `https://github.com/kpucynski/ha-mojdomek` with type **Integration**.
3. Search for **mojdomek.eu**, download it, and restart Home Assistant.

### Manual

Copy `custom_components/mojdomek` into the `custom_components` folder of your Home Assistant configuration directory and restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up the integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=mojdomek)

Go to **Settings → Devices & services → Add integration**, search for **mojdomek.eu**, and enter:

| Field | Description |
| --- | --- |
| Account ID | The `id` value from your mojdomek.eu API link, e.g. `https://mojdomek.eu/api/api2.php?id=…` |
| Device | Which liquid level sensor of that account to add |

You can add multiple devices from the same account by running the config flow again.

## API

The integration uses the public JSON endpoint:

`https://mojdomek.eu/api/api2.php?id=<account_id>`

Timestamps from the API are treated as Europe/Warsaw local time.

## Removal

Remove the integration under **Settings → Devices & services**, then remove the repository in HACS.
