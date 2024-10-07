"""iAlarm integration."""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import IAlarmCoordinator
from .pyialarm.pyialarm import IAlarm

PLATFORMS = [Platform.ALARM_CONTROL_PANEL, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iAlarm config."""
    host: str = entry.data[CONF_HOST]
    port: int = entry.data[CONF_PORT]
    ialarm = IAlarm(host, port)

    try:
        async with asyncio.timeout(10):
            mac = await ialarm.get_mac()
    except (TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    statusCoordinator = IAlarmCoordinator(hass, ialarm, mac)

    async def _async_on_hass_stop(_: Event) -> None:
        """Close connection when hass stops."""
        await statusCoordinator.async_shutdown()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_on_hass_stop)
    )

    await statusCoordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: statusCoordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload iAlarm config."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
