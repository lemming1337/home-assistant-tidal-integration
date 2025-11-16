"""Services for Tidal integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_ADD_TO_PLAYLIST,
    SERVICE_CREATE_PLAYLIST,
    SERVICE_LIKE_TRACK,
    SERVICE_PLAY_ALBUM,
    SERVICE_PLAY_ARTIST,
    SERVICE_PLAY_PLAYLIST,
    SERVICE_PLAY_TRACK,
    SERVICE_REMOVE_FROM_PLAYLIST,
    SERVICE_UNLIKE_TRACK,
)
from .coordinator import TidalDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
PLAY_PLAYLIST_SCHEMA = vol.Schema(
    {
        vol.Required("playlist_id"): cv.string,
        vol.Optional("entity_id"): cv.entity_id,
    }
)

PLAY_ALBUM_SCHEMA = vol.Schema(
    {
        vol.Required("album_id"): cv.string,
        vol.Optional("entity_id"): cv.entity_id,
    }
)

PLAY_TRACK_SCHEMA = vol.Schema(
    {
        vol.Required("track_id"): cv.string,
        vol.Optional("entity_id"): cv.entity_id,
    }
)

PLAY_ARTIST_SCHEMA = vol.Schema(
    {
        vol.Required("artist_id"): cv.string,
        vol.Optional("entity_id"): cv.entity_id,
    }
)

ADD_TO_PLAYLIST_SCHEMA = vol.Schema(
    {
        vol.Required("playlist_id"): cv.string,
        vol.Required("track_ids"): vol.All(cv.ensure_list, [cv.string]),
    }
)

REMOVE_FROM_PLAYLIST_SCHEMA = vol.Schema(
    {
        vol.Required("playlist_id"): cv.string,
        vol.Required("track_ids"): vol.All(cv.ensure_list, [cv.string]),
    }
)

CREATE_PLAYLIST_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("description", default=""): cv.string,
    }
)

LIKE_TRACK_SCHEMA = vol.Schema(
    {
        vol.Required("track_id"): cv.string,
    }
)

UNLIKE_TRACK_SCHEMA = vol.Schema(
    {
        vol.Required("track_id"): cv.string,
    }
)


async def async_setup_services(
    hass: HomeAssistant, coordinator: TidalDataUpdateCoordinator
) -> None:
    """Set up services for Tidal integration.

    Args:
        hass: Home Assistant instance
        coordinator: Data update coordinator
    """

    async def handle_play_playlist(call: ServiceCall) -> None:
        """Handle play playlist service call.

        Args:
            call: Service call
        """
        playlist_id = call.data["playlist_id"]
        entity_id = call.data.get("entity_id")

        _LOGGER.debug("Playing playlist: %s", playlist_id)

        # Get the media player entity
        if entity_id:
            # Play on specific entity
            await hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": entity_id,
                    "media_content_type": "playlist",
                    "media_content_id": playlist_id,
                },
            )

    async def handle_play_album(call: ServiceCall) -> None:
        """Handle play album service call.

        Args:
            call: Service call
        """
        album_id = call.data["album_id"]
        entity_id = call.data.get("entity_id")

        _LOGGER.debug("Playing album: %s", album_id)

        # Get the media player entity
        if entity_id:
            # Play on specific entity
            await hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": entity_id,
                    "media_content_type": "album",
                    "media_content_id": album_id,
                },
            )

    async def handle_play_track(call: ServiceCall) -> None:
        """Handle play track service call.

        Args:
            call: Service call
        """
        track_id = call.data["track_id"]
        entity_id = call.data.get("entity_id")

        _LOGGER.debug("Playing track: %s", track_id)

        # Get the media player entity
        if entity_id:
            # Play on specific entity
            await hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": entity_id,
                    "media_content_type": "track",
                    "media_content_id": track_id,
                },
            )

    async def handle_play_artist(call: ServiceCall) -> None:
        """Handle play artist service call.

        Args:
            call: Service call
        """
        artist_id = call.data["artist_id"]
        entity_id = call.data.get("entity_id")

        _LOGGER.debug("Playing artist: %s", artist_id)

        # Get the media player entity
        if entity_id:
            # Play on specific entity
            await hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": entity_id,
                    "media_content_type": "artist",
                    "media_content_id": artist_id,
                },
            )

    async def handle_add_to_playlist(call: ServiceCall) -> None:
        """Handle add to playlist service call.

        Args:
            call: Service call
        """
        playlist_id = call.data["playlist_id"]
        track_ids = call.data["track_ids"]

        _LOGGER.debug("Adding tracks to playlist %s: %s", playlist_id, track_ids)

        try:
            await coordinator.api.add_to_playlist(playlist_id, track_ids)
            # Refresh data to update sensors
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error adding to playlist: %s", err)

    async def handle_remove_from_playlist(call: ServiceCall) -> None:
        """Handle remove from playlist service call.

        Args:
            call: Service call
        """
        playlist_id = call.data["playlist_id"]
        track_ids = call.data["track_ids"]

        _LOGGER.debug("Removing tracks from playlist %s: %s", playlist_id, track_ids)

        try:
            await coordinator.api.remove_from_playlist(playlist_id, track_ids)
            # Refresh data to update sensors
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error removing from playlist: %s", err)

    async def handle_create_playlist(call: ServiceCall) -> None:
        """Handle create playlist service call.

        Args:
            call: Service call
        """
        name = call.data["name"]
        description = call.data.get("description", "")

        _LOGGER.debug("Creating playlist: %s", name)

        try:
            await coordinator.api.create_playlist(name, description)
            # Refresh data to update sensors
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error creating playlist: %s", err)

    async def handle_like_track(call: ServiceCall) -> None:
        """Handle like track service call.

        Args:
            call: Service call
        """
        track_id = call.data["track_id"]

        _LOGGER.debug("Liking track: %s", track_id)

        try:
            await coordinator.api.add_favorite_track(track_id)
            # Refresh data to update sensors
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error liking track: %s", err)

    async def handle_unlike_track(call: ServiceCall) -> None:
        """Handle unlike track service call.

        Args:
            call: Service call
        """
        track_id = call.data["track_id"]

        _LOGGER.debug("Unliking track: %s", track_id)

        try:
            await coordinator.api.remove_favorite_track(track_id)
            # Refresh data to update sensors
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error unliking track: %s", err)

    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_PLAYLIST, handle_play_playlist, schema=PLAY_PLAYLIST_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_ALBUM, handle_play_album, schema=PLAY_ALBUM_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_TRACK, handle_play_track, schema=PLAY_TRACK_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_ARTIST, handle_play_artist, schema=PLAY_ARTIST_SCHEMA
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TO_PLAYLIST,
        handle_add_to_playlist,
        schema=ADD_TO_PLAYLIST_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_FROM_PLAYLIST,
        handle_remove_from_playlist,
        schema=REMOVE_FROM_PLAYLIST_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_PLAYLIST,
        handle_create_playlist,
        schema=CREATE_PLAYLIST_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN, SERVICE_LIKE_TRACK, handle_like_track, schema=LIKE_TRACK_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, SERVICE_UNLIKE_TRACK, handle_unlike_track, schema=UNLIKE_TRACK_SCHEMA
    )

    _LOGGER.debug("Tidal services registered")
