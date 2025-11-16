"""Config flow for Tidal integration."""
from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from typing import Any
from urllib.parse import urlencode

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TidalAPI, TidalAuthError, TidalConnectionError
from .const import (
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

TIDAL_AUTH_URL = "https://login.tidal.com/authorize"
TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"


class TidalFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Tidal config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._country_code: str | None = None
        self._code_verifier: str | None = None
        self._state: str | None = None
        self._redirect_uri: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - collect Client ID, Secret, and Country Code."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID]
            self._client_secret = user_input[CONF_CLIENT_SECRET]
            self._country_code = user_input.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE)

            # Generate PKCE code verifier and challenge
            self._code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip("=")
            code_challenge = hashlib.sha256(self._code_verifier.encode('utf-8')).digest()
            code_challenge_b64 = base64.urlsafe_b64encode(code_challenge).decode('utf-8').rstrip("=")

            # Generate state for CSRF protection
            self._state = secrets.token_urlsafe(32)

            # Build redirect URI
            self._redirect_uri = f"{self.hass.config.api.base_url}/auth/external/callback"

            # Build authorization URL
            scopes = "r_usr w_usr"
            auth_url = (
                f"{TIDAL_AUTH_URL}"
                f"?response_type=code"
                f"&client_id={self._client_id}"
                f"&redirect_uri={self._redirect_uri}"
                f"&scope={scopes}"
                f"&code_challenge_method=S256"
                f"&code_challenge={code_challenge_b64}"
                f"&state={self._state}"
            )

            return self.async_external_step(step_id="authorize", url=auth_url)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Optional(CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE): str,
                }
            ),
            errors=errors,
        )

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle authorization callback."""
        if user_input is None:
            return self.async_abort(reason="missing_credentials")

        # Verify state
        if user_input.get("state") != self._state:
            return self.async_abort(reason="invalid_state")

        code = user_input.get("code")
        if not code:
            return self.async_abort(reason="missing_code")

        # Exchange authorization code for access token
        try:
            session = async_get_clientsession(self.hass)

            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": self._redirect_uri,
                "code_verifier": self._code_verifier,
            }

            async with session.post(TIDAL_TOKEN_URL, data=token_data) as response:
                response.raise_for_status()
                token_response = await response.json()

            access_token = token_response["access_token"]
            refresh_token = token_response.get("refresh_token")

            # Get user ID from /users/me endpoint
            api = TidalAPI(
                session=session,
                client_id=self._client_id,
                client_secret=self._client_secret,
                user_id="",  # Temporary, will be updated after getting user info
                country_code=self._country_code or DEFAULT_COUNTRY_CODE,
            )
            await api.authenticate(access_token, refresh_token)

            # Call /users/me to get the user ID
            user_data = await api.get_current_user()
            user_id = user_data.get("id")

            if not user_id:
                _LOGGER.error("Failed to retrieve user ID from /users/me endpoint")
                return self.async_abort(reason=ERROR_AUTH_FAILED)

            # Set unique ID
            await self.async_set_unique_id(str(user_id))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Tidal - {user_id}",
                data={
                    CONF_CLIENT_ID: self._client_id,
                    CONF_CLIENT_SECRET: self._client_secret,
                    CONF_USER_ID: str(user_id),
                    CONF_ACCESS_TOKEN: access_token,
                    "refresh_token": refresh_token,
                    CONF_COUNTRY_CODE: self._country_code or DEFAULT_COUNTRY_CODE,
                },
            )

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Error during token exchange: %s", err)
            return self.async_abort(reason=ERROR_AUTH_FAILED)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthorization request."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm reauthorization."""
        errors: dict[str, str] = {}

        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if entry is None:
            return self.async_abort(reason="reauth_failed")

        if user_input is not None:
            # Start OAuth flow again
            self._client_id = user_input.get(CONF_CLIENT_ID, entry.data.get(CONF_CLIENT_ID))
            self._client_secret = user_input.get(CONF_CLIENT_SECRET, entry.data.get(CONF_CLIENT_SECRET))

            # Restart OAuth flow
            return await self.async_step_user({
                CONF_CLIENT_ID: self._client_id,
                CONF_CLIENT_SECRET: self._client_secret,
            })

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID, default=entry.data.get(CONF_CLIENT_ID)): str,
                    vol.Required(CONF_CLIENT_SECRET, default=entry.data.get(CONF_CLIENT_SECRET)): str,
                }
            ),
            errors=errors,
        )


class TidalOptionsFlow(config_entries.OptionsFlow):
    """Handle Tidal options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Tidal options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
