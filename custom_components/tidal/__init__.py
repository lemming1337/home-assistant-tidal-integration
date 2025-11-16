"""The Tidal integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
)

from .api import TidalAPI, TidalAuthError, TidalConnectionError
from .const import (
    CONF_COUNTRY_CODE,
    CONF_USER_ID,
    DEFAULT_COUNTRY_CODE,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import TidalDataUpdateCoordinator

if TYPE_CHECKING:
    pass

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
    _LOGGER.debug("Setting up Tidal integration for user %s", entry.data.get(CONF_USER_ID))

    # Get OAuth2 implementation
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = aiohttp_client.async_get_clientsession(hass)

    # Get access token from entry data
    token = entry.data.get("token", {})
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")

    if not access_token:
        # Try legacy format
        access_token = entry.data.get(CONF_ACCESS_TOKEN)
        refresh_token = entry.data.get("refresh_token")

    if not access_token:
        _LOGGER.error("No access token found in config entry")
        raise ConfigEntryAuthFailed("No access token found")

    # Create API client
    api = TidalAPI(
        session=session,
        client_id=implementation.client_id,
        client_secret=implementation.client_secret,
        user_id=entry.data[CONF_USER_ID],
        country_code=entry.data.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
    )

    # Authenticate
    try:
        await api.authenticate(access_token=access_token, refresh_token=refresh_token)
    except TidalAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except TidalConnectionError as err:
        _LOGGER.error("Connection failed: %s", err)
        raise ConfigEntryNotReady(f"Connection failed: {err}") from err

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

    _LOGGER.info("Tidal integration setup complete for user %s", entry.data.get(CONF_USER_ID))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TidalConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if unload was successful
    """
    _LOGGER.debug("Unloading Tidal integration for user %s", entry.data.get(CONF_USER_ID))

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        _LOGGER.info("Tidal integration unloaded for user %s", entry.data.get(CONF_USER_ID))

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
