"""Interfaces with iAlarm control panels."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, IAlarmStatusType
from .coordinator import IAlarmCoordinator
from .pyialarm.const import LogEntryType

_LOGGER = logging.getLogger(__name__)

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required("max_entries"): vol.Coerce(int),
    }
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a iAlarm alarm control panel based on a config entry."""
    ialarm_coordinator: IAlarmCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([IAlarmPanel(ialarm_coordinator)], False)

    # Registrazione del servizio dopo aver configurato l'entrata
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "get_log",
        ACTION_SCHEMA,
        "async_last_log_entries",
    )


class IAlarmPanel(CoordinatorEntity[IAlarmCoordinator], AlarmControlPanelEntity):
    """Representation of an iAlarm device."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )
    _attr_code_arm_required = False

    def __init__(self, coordinator: IAlarmCoordinator) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.mac)},
            manufacturer="Antifurto365 - Meian",
            name="iAlarm",
        )
        self._attr_unique_id = f"{coordinator.mac}-ialarm_status"

    @property
    def state(self) -> str | None:
        """Return the state of the device."""
        ialarm_state: IAlarmStatusType | None = self.coordinator.state
        if ialarm_state is None:
            return None
        return ialarm_state["ialarm_status"]

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        # Require a code to be passed for disarm operations
        if code is None or code == "":
            raise ValueError("Please input the disarm code.")
        await self.coordinator.ialarm.disarm()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.coordinator.ialarm.arm_stay()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.coordinator.ialarm.arm_away()

    async def async_last_log_entries(self, max_entries: int) -> list[LogEntryType]:
        """Retrieve last n log entries."""
        return await self.coordinator.ialarm.get_last_log_entries(max_entries)
