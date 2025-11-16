"""Application credentials platform for Tidal."""
from __future__ import annotations

from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

from .const import DOMAIN, OAUTH_SCOPES

OAUTH2_AUTHORIZE = "https://login.tidal.com/authorize"
OAUTH2_TOKEN = "https://auth.tidal.com/v1/oauth2/token"


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server configuration for Tidal OAuth2."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
    )


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials dialog."""
    return {
        "oauth_url": "https://developer.tidal.com/dashboard",
        "more_info_url": "https://developer.tidal.com/documentation/api/api-overview#authorization",
    }
