"""Constants for the Tidal integration."""
from typing import Final

# Integration domain
DOMAIN: Final = "tidal"

# Configuration constants
CONF_USER_ID: Final = "user_id"
CONF_API_KEY: Final = "api_key"
CONF_CLIENT_ID: Final = "client_id"
CONF_CLIENT_SECRET: Final = "client_secret"
CONF_COUNTRY_CODE: Final = "country_code"

# Default values
DEFAULT_NAME: Final = "Tidal"
DEFAULT_COUNTRY_CODE: Final = "US"

# API constants
API_BASE_URL: Final = "https://openapi.tidal.com/v2"
API_AUTH_URL: Final = "https://auth.tidal.com/v1/oauth2"
API_TOKEN_URL: Final = "https://auth.tidal.com/v1/oauth2/token"

# OAuth2 scopes
OAUTH_SCOPES: Final = [
    "user.read",
    "playlists.read",
    "playlists.write",
    "collection.read",
    "playback",
    "search.read",
]

# Platforms
PLATFORMS: Final = ["media_player", "sensor"]

# Update intervals (in seconds)
UPDATE_INTERVAL: Final = 30
TOKEN_REFRESH_INTERVAL: Final = 3600

# Media player constants
SUPPORTED_MEDIA_TYPES: Final = {
    "track": "music",
    "album": "album",
    "playlist": "playlist",
    "artist": "artist",
    "video": "video",
}

# Service names
SERVICE_PLAY_PLAYLIST: Final = "play_playlist"
SERVICE_PLAY_ALBUM: Final = "play_album"
SERVICE_PLAY_TRACK: Final = "play_track"
SERVICE_PLAY_ARTIST: Final = "play_artist"
SERVICE_ADD_TO_PLAYLIST: Final = "add_to_playlist"
SERVICE_REMOVE_FROM_PLAYLIST: Final = "remove_from_playlist"
SERVICE_CREATE_PLAYLIST: Final = "create_playlist"
SERVICE_LIKE_TRACK: Final = "like_track"
SERVICE_UNLIKE_TRACK: Final = "unlike_track"

# Sensor types
SENSOR_FAVORITE_TRACKS: Final = "favorite_tracks"
SENSOR_FAVORITE_ALBUMS: Final = "favorite_albums"
SENSOR_FAVORITE_ARTISTS: Final = "favorite_artists"
SENSOR_PLAYLISTS: Final = "playlists"

# Attribution
ATTRIBUTION: Final = "Data provided by Tidal"

# Error messages
ERROR_AUTH_FAILED: Final = "authentication_failed"
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_INVALID_AUTH: Final = "invalid_auth"
ERROR_UNKNOWN: Final = "unknown_error"

# LLM Tool names
TOOL_GET_PLAYLISTS: Final = "tidal_get_playlists"
TOOL_GET_ALBUMS: Final = "tidal_get_albums"
TOOL_GET_TRACKS: Final = "tidal_get_tracks"
TOOL_GET_ARTISTS: Final = "tidal_get_artists"
TOOL_PLAY_CONTENT: Final = "tidal_play_content"
TOOL_SEARCH: Final = "tidal_search"
