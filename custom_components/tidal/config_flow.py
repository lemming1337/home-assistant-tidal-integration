"""Config flow for Tidal integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE_URL,
    CONF_COUNTRY_CODE,
    CONF_USER_ID,
    DEFAULT_COUNTRY_CODE,
    DOMAIN,
    ERROR_AUTH_FAILED,
    OAUTH_SCOPES,
)

_LOGGER = logging.getLogger(__name__)


class TidalFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a Tidal config flow."""

    DOMAIN = DOMAIN
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._country_code: str | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TidalOptionsFlow(config_entry)

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": " ".join(OAUTH_SCOPES),
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step - collect Country Code."""
        if user_input is not None:
            self._country_code = user_input.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE)
            return await super().async_step_user()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE): str,
                }
            ),
        )

    async def async_oauth_create_entry(
        self, data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Create an entry for the flow."""
        # Get OAuth2 implementation
        implementation = await self.async_get_implementation()

        # Create a temporary config entry-like object for OAuth2Session
        # We need to use a simple session with access token for initial user info fetch
        session = async_get_clientsession(self.hass)

        # Get user ID from /users/me endpoint by making a direct API call
        try:
            headers = {
                "Authorization": f"Bearer {data['token']['access_token']}",
                "Content-Type": "application/vnd.api+json",
            }

            async with session.get(
                f"{API_BASE_URL}/users/me",
                headers=headers,
                params={"countryCode": self._country_code or DEFAULT_COUNTRY_CODE}
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
                user_data = response_data.get("data", {})
                user_id = user_data.get("id")

            if not user_id:
                _LOGGER.error("Failed to retrieve user ID from /users/me endpoint")
                return self.async_abort(reason=ERROR_AUTH_FAILED)

        except Exception as err:
            _LOGGER.exception("Error getting user info: %s", err)
            return self.async_abort(reason=ERROR_AUTH_FAILED)

        # Store user_id and country_code in data
        data[CONF_USER_ID] = str(user_id)
        data[CONF_COUNTRY_CODE] = self._country_code or DEFAULT_COUNTRY_CODE

        # Set unique ID and check if already configured
        await self.async_set_unique_id(str(user_id))

        if self._reauth_entry:
            # Update existing entry during reauth
            self.hass.config_entries.async_update_entry(
                self._reauth_entry,
                data=data,
            )
            await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Tidal - {user_id}",
            data=data,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthorization request."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm reauthorization."""
        if user_input is not None:
            # Get country code from existing entry
            if self._reauth_entry:
                self._country_code = self._reauth_entry.data.get(
                    CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE
                )
            return await super().async_step_user()

        return self.async_show_form(
            step_id="reauth_confirm",
            description_placeholders={
                "account": self._reauth_entry.data.get(CONF_USER_ID, "")
                if self._reauth_entry
                else "",
            },
        )


class TidalOptionsFlow(config_entries.OptionsFlow):
    """Handle Tidal options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Tidal options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
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
