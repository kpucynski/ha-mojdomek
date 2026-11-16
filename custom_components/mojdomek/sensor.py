"""Sensors for a mojdomek.eu liquid level sensor."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import MojdomekDevice
from .const import DOMAIN
from .coordinator import MojdomekConfigEntry, MojdomekCoordinator

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class MojdomekSensorDescription(SensorEntityDescription):
    """Describes a liquid level sensor entity."""

    value_fn: Callable[[MojdomekDevice], float | datetime | None]


SENSORS: tuple[MojdomekSensorDescription, ...] = (
    MojdomekSensorDescription(
        key="fill_level",
        translation_key="fill_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.fill_level,
    ),
    MojdomekSensorDescription(
        key="level",
        translation_key="level",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        value_fn=lambda device: device.level,
    ),
    MojdomekSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda device: device.temperature,
    ),
    MojdomekSensorDescription(
        key="predicted_full",
        translation_key="predicted_full",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda device: device.predicted_full,
    ),
    MojdomekSensorDescription(
        key="last_emptied",
        translation_key="last_emptied",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda device: device.last_emptied,
    ),
    MojdomekSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.battery_level,
    ),
    MojdomekSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.battery_voltage,
    ),
    MojdomekSensorDescription(
        key="signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.signal_strength,
    ),
    MojdomekSensorDescription(
        key="last_measurement",
        translation_key="last_measurement",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.measured_at,
    ),
    MojdomekSensorDescription(
        key="alarm_level",
        translation_key="alarm_level",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.alarm_level,
    ),
    MojdomekSensorDescription(
        key="max_level",
        translation_key="max_level",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.max_level,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MojdomekConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors of a liquid level sensor."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        MojdomekSensor(coordinator, description) for description in SENSORS
    )


class MojdomekSensor(CoordinatorEntity[MojdomekCoordinator], SensorEntity):
    """A value reported by a liquid level sensor."""

    _attr_has_entity_name = True
    entity_description: MojdomekSensorDescription

    def __init__(
        self,
        coordinator: MojdomekCoordinator,
        description: MojdomekSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        device = coordinator.data
        self._attr_unique_id = f"{device.id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            name=device.name,
            manufacturer="mojdomek.eu",
            model=device.model,
            sw_version=device.software,
            serial_number=device.id,
        )

    @property
    def native_value(self) -> float | datetime | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
