"""DataUpdateCoordinator for the Tidal integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import TidalAPI, TidalAuthError, TidalConnectionError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class TidalDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Tidal data."""

    def __init__(self, hass: HomeAssistant, api: TidalAPI) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api: Tidal API client
        """
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Tidal API.

        Returns:
            Dictionary containing all user data

        Raises:
            UpdateFailed: If update fails
        """
        try:
            # Fetch all user data
            playlists = await self.api.get_user_playlists()
            albums = await self.api.get_user_albums()
            tracks = await self.api.get_user_tracks()
            artists = await self.api.get_user_artists()

            return {
                "playlists": playlists,
                "albums": albums,
                "tracks": tracks,
                "artists": artists,
            }

        except TidalAuthError as err:
            _LOGGER.error("Authentication error during update: %s", err)
            raise UpdateFailed(f"Authentication error: {err}") from err
        except TidalConnectionError as err:
            _LOGGER.error("Connection error during update: %s", err)
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during update")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_get_playlist_tracks(self, playlist_id: str) -> list[dict[str, Any]]:
        """Get tracks from a playlist.

        Args:
            playlist_id: Playlist ID

        Returns:
            List of track data

        Raises:
            UpdateFailed: If fetching fails
        """
        try:
            playlist = await self.api.get_playlist(playlist_id)
            # Extract tracks from relationships if available
            if "relationships" in playlist and "tracks" in playlist["relationships"]:
                track_ids = [
                    track["id"]
                    for track in playlist["relationships"]["tracks"].get("data", [])
                ]
                # Fetch full track details
                tracks = []
                for track_id in track_ids:
                    track = await self.api.get_track(track_id)
                    tracks.append(track)
                return tracks
            return []
        except (TidalAuthError, TidalConnectionError) as err:
            _LOGGER.error("Error fetching playlist tracks: %s", err)
            raise UpdateFailed(f"Error fetching playlist tracks: {err}") from err

    async def async_get_album_tracks(self, album_id: str) -> list[dict[str, Any]]:
        """Get tracks from an album.

        Args:
            album_id: Album ID

        Returns:
            List of track data

        Raises:
            UpdateFailed: If fetching fails
        """
        try:
            album = await self.api.get_album(album_id)
            # Extract tracks from relationships if available
            if "relationships" in album and "tracks" in album["relationships"]:
                track_ids = [
                    track["id"]
                    for track in album["relationships"]["tracks"].get("data", [])
                ]
                # Fetch full track details
                tracks = []
                for track_id in track_ids:
                    track = await self.api.get_track(track_id)
                    tracks.append(track)
                return tracks
            return []
        except (TidalAuthError, TidalConnectionError) as err:
            _LOGGER.error("Error fetching album tracks: %s", err)
            raise UpdateFailed(f"Error fetching album tracks: {err}") from err

    async def async_search(
        self, query: str, search_type: str | None = None
    ) -> dict[str, Any]:
        """Search for content.

        Args:
            query: Search query
            search_type: Type of content to search

        Returns:
            Search results

        Raises:
            UpdateFailed: If search fails
        """
        try:
            return await self.api.search(query, search_type)
        except (TidalAuthError, TidalConnectionError) as err:
            _LOGGER.error("Error searching: %s", err)
            raise UpdateFailed(f"Error searching: {err}") from err

    @property
    def playlists(self) -> list[dict[str, Any]]:
        """Get user playlists."""
        if self.data:
            return self.data.get("playlists", [])
        return []

    @property
    def albums(self) -> list[dict[str, Any]]:
        """Get user albums."""
        if self.data:
            return self.data.get("albums", [])
        return []

    @property
    def tracks(self) -> list[dict[str, Any]]:
        """Get user tracks."""
        if self.data:
            return self.data.get("tracks", [])
        return []

    @property
    def artists(self) -> list[dict[str, Any]]:
        """Get user artists."""
        if self.data:
            return self.data.get("artists", [])
        return []
