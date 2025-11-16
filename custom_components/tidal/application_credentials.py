"""Application credentials platform for Tidal."""
from __future__ import annotations

import base64
import hashlib
import secrets

from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN

OAUTH2_AUTHORIZE = "https://login.tidal.com/authorize"
OAUTH2_TOKEN = "https://auth.tidal.com/v1/oauth2/token"


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return auth implementation with PKCE support.

    Tidal requires PKCE (Proof Key for Code Exchange) for all OAuth2 flows.
    """
    # Use LocalOAuth2Implementation with PKCE enabled
    # PKCE is required by Tidal API (OAuth 2.1)
    implementation = TidalOAuth2Implementation(
        hass,
        DOMAIN,
        credential,
        authorization_server=AuthorizationServer(
            authorize_url=OAUTH2_AUTHORIZE,
            token_url=OAUTH2_TOKEN,
        ),
    )
    return implementation


class TidalOAuth2Implementation(config_entry_oauth2_flow.LocalOAuth2Implementation):
    """Tidal OAuth2 implementation with PKCE support."""

    def __init__(
        self,
        hass: HomeAssistant,
        domain: str,
        credential: ClientCredential,
        authorization_server: AuthorizationServer,
    ) -> None:
        """Initialize Tidal OAuth2 implementation."""
        super().__init__(
            hass,
            domain,
            credential,
            authorization_server,
        )
        # Generate PKCE code verifier (43-128 characters, base64url encoded)
        self._code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode("utf-8").rstrip("=")

    def _generate_code_challenge(self) -> str:
        """Generate PKCE code challenge from verifier using SHA256."""
        code_challenge = hashlib.sha256(
            self._code_verifier.encode("utf-8")
        ).digest()
        return base64.urlsafe_b64encode(code_challenge).decode("utf-8").rstrip("=")

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data to include in authorization request."""
        data = super().extra_authorize_data
        # Add PKCE parameters required by Tidal
        data.update({
            "code_challenge": self._generate_code_challenge(),
            "code_challenge_method": "S256",
        })
        return data

    async def async_resolve_external_data(self, external_data: dict) -> dict:
        """Resolve external data to tokens, including code_verifier for PKCE."""
        # Add code_verifier to token request as required by PKCE
        return await super().async_resolve_external_data(external_data)

    async def _token_request(self, data: dict) -> dict:
        """Make a token request with PKCE code_verifier."""
        # Add code_verifier to token request
        data["code_verifier"] = self._code_verifier
        return await super()._token_request(data)


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server configuration for Tidal OAuth2."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
    )


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials dialog."""
    # Get the OAuth2 redirect URI that should be configured in Tidal Developer Portal
    redirect_uri = config_entry_oauth2_flow.async_get_redirect_uri(hass)

    return {
        "oauth_url": "https://developer.tidal.com/dashboard",
        "more_info_url": "https://developer.tidal.com/documentation/api/api-overview#authorization",
        "redirect_uri": redirect_uri,
    }
