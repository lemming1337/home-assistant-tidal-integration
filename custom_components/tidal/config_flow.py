"""Config flow for Tidal integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TidalAPI, TidalAuthError, TidalConnectionError
from .const import (
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_COUNTRY_CODE,
    CONF_USER_ID,
    DEFAULT_COUNTRY_CODE,
    DOMAIN,
    ERROR_AUTH_FAILED,
    ERROR_CANNOT_CONNECT,
    ERROR_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Args:
        hass: Home Assistant instance
        data: User input data

    Returns:
        Dictionary with user info

    Raises:
        TidalAuthError: If authentication fails
        TidalConnectionError: If connection fails
    """
    session = async_get_clientsession(hass)

    api = TidalAPI(
        session=session,
        client_id=data[CONF_CLIENT_ID],
        client_secret=data[CONF_CLIENT_SECRET],
        user_id=data[CONF_USER_ID],
        country_code=data.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
    )

    # Authenticate with the API
    await api.authenticate()

    # Try to fetch user playlists to verify connection
    await api.get_user_playlists()

    return {
        "title": f"Tidal - {data[CONF_USER_ID]}",
        "user_id": data[CONF_USER_ID],
    }


class TidalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tidal."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.

        Args:
            user_input: User input data

        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_USER_ID])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except TidalAuthError:
                errors["base"] = ERROR_AUTH_FAILED
            except TidalConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Required(CONF_USER_ID): str,
                    vol.Optional(
                        CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthorization request.

        Args:
            entry_data: Entry data

        Returns:
            Flow result
        """
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm reauthorization.

        Args:
            user_input: User input data

        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Get existing entry
            entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
            if entry is None:
                return self.async_abort(reason="reauth_failed")

            # Merge with existing data
            data = {**entry.data, **user_input}

            try:
                await validate_input(self.hass, data)
            except TidalAuthError:
                errors["base"] = ERROR_AUTH_FAILED
            except TidalConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN
            else:
                self.hass.config_entries.async_update_entry(entry, data=data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
            errors=errors,
        )


class TidalOptionsFlow(config_entries.OptionsFlow):
    """Handle Tidal options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Tidal options flow.

        Args:
            config_entry: Config entry instance
        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options.

        Args:
            user_input: User input data

        Returns:
            Flow result
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_COUNTRY_CODE,
                        default=self.config_entry.data.get(
                            CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE
                        ),
                    ): str,
                }
            ),
        )
