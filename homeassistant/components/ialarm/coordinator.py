"""Coordinator for the iAlarm integration."""

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, IALARM_TO_HASS, IAlarmStatusType
from .pyialarm.const import ZoneStatusType
from .pyialarm.pyialarm import IAlarm

_LOGGER = logging.getLogger(__name__)


class IAlarmCoordinator(DataUpdateCoordinator[IAlarmStatusType]):
    """Class to manage fetching iAlarm data."""

    def __init__(self, hass: HomeAssistant, ialarm: IAlarm, mac: str) -> None:
        """Initialize global iAlarm data updater."""
        self.ialarm = ialarm
        self.state: IAlarmStatusType | None = None
        self.host: str = ialarm.host
        self.mac = mac

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> IAlarmStatusType:
        """Fetch data from iAlarm."""
        try:
            status = await self.ialarm.get_status()
            zone_status: list[ZoneStatusType] = await self.ialarm.get_zone_status()
            ialarm_status: IAlarmStatusType = IAlarmStatusType(
                ialarm_status=IALARM_TO_HASS.get(status), zone_status_list=zone_status
            )
            self.state = ialarm_status
            self.async_set_updated_data(ialarm_status)
        except ConnectionError as error:
            raise UpdateFailed(error) from error
        return ialarm_status
