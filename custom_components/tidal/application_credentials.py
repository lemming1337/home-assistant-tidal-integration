"""Application credentials platform for Tidal."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2Implementation,
    LocalOAuth2ImplementationWithPkce,
)
from homeassistant.components.application_credentials import (
    ClientCredential,
    AuthorizationServer,
)

OAUTH2_AUTHORIZE = "https://login.tidal.com/authorize"
OAUTH2_TOKEN = "https://auth.tidal.com/v1/oauth2/token"


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    return AuthorizationServer(authorize_url=OAUTH2_AUTHORIZE, token_url=OAUTH2_TOKEN)


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> AbstractOAuth2Implementation:
    """Return auth implementation with PKCE support.

    Tidal requires PKCE (Proof Key for Code Exchange) for all OAuth2 flows.
    """
    # Use LocalOAuth2Implementation with PKCE enabled
    # PKCE is required by Tidal API (OAuth 2.1)
    implementation = LocalOAuth2ImplementationWithPkce(
        hass,
        auth_domain,
        credential.client_id,
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
        client_secret=credential.client_secret,  # optional `""` is default
        code_verifier_length=128,  # optional
    )

    return implementation
