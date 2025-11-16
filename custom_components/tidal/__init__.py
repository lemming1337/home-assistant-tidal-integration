"""The Tidal integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TidalAPI, TidalAuthError, TidalConnectionError
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_COUNTRY_CODE,
    CONF_USER_ID,
    DEFAULT_COUNTRY_CODE,
    DOMAIN,
    PLATFORMS,
)

if TYPE_CHECKING:
    from .coordinator import TidalDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

type TidalConfigEntry = ConfigEntry[TidalDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TidalConfigEntry) -> bool:
    """Set up Tidal from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if setup was successful

    Raises:
        ConfigEntryAuthFailed: If authentication fails
        ConfigEntryNotReady: If connection fails
    """
    _LOGGER.debug("Setting up Tidal integration for user %s", entry.data[CONF_USER_ID])

    session = async_get_clientsession(hass)

    # Create API client
    api = TidalAPI(
        session=session,
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
        user_id=entry.data[CONF_USER_ID],
        country_code=entry.data.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
    )

    # Authenticate
    try:
        await api.authenticate()
    except TidalAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except TidalConnectionError as err:
        _LOGGER.error("Connection failed: %s", err)
        raise ConfigEntryNotReady(f"Connection failed: {err}") from err

    # Import here to avoid circular dependency
    from .coordinator import TidalDataUpdateCoordinator

    # Create coordinator
    coordinator = TidalDataUpdateCoordinator(hass, api)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    entry.runtime_data = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass, coordinator)

    # Register LLM tools
    await async_setup_llm_tools(hass, entry)

    _LOGGER.info("Tidal integration setup complete for user %s", entry.data[CONF_USER_ID])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TidalConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if unload was successful
    """
    _LOGGER.debug("Unloading Tidal integration for user %s", entry.data[CONF_USER_ID])

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        _LOGGER.info("Tidal integration unloaded for user %s", entry.data[CONF_USER_ID])

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: TidalConfigEntry) -> None:
    """Reload config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_setup_services(
    hass: HomeAssistant, coordinator: TidalDataUpdateCoordinator
) -> None:
    """Set up Tidal services.

    Args:
        hass: Home Assistant instance
        coordinator: Data update coordinator
    """
    # Import services module
    from . import services

    # Register services
    await services.async_setup_services(hass, coordinator)


async def async_setup_llm_tools(hass: HomeAssistant, entry: TidalConfigEntry) -> None:
    """Set up LLM tools for Tidal.

    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    # Import LLM tools module
    from . import llm_tools

    # Register LLM tools
    await llm_tools.async_setup_llm_tools(hass, entry)
