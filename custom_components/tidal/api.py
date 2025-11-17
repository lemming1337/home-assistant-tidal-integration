"""Tidal API Client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientResponseError

from homeassistant.helpers import config_entry_oauth2_flow

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class TidalAuthError(Exception):
    """Exception to indicate authentication failure."""


class TidalConnectionError(Exception):
    """Exception to indicate connection failure."""


class TidalAPI:
    """Tidal API Client."""

    def __init__(
        self,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
        user_id: str,
        country_code: str = "DE",
    ) -> None:
        """Initialize the Tidal API client.

        Args:
            oauth_session: OAuth2 session from Home Assistant
            user_id: Tidal user ID
            country_code: ISO 3166-1 country code
        """
        self._oauth_session = oauth_session
        self._user_id = user_id
        self._country_code = country_code

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a request to the Tidal API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to the request

        Returns:
            Response data as dictionary

        Raises:
            TidalAuthError: If authentication fails
            TidalConnectionError: If connection fails
        """
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/vnd.api+json"

        # Add country code to params if not already present
        params = kwargs.get("params", {})
        if "countryCode" not in params:
            params["countryCode"] = self._country_code
        kwargs["params"] = params

        try:
            response = await self._oauth_session.async_request(
                method, url, headers=headers, **kwargs
            )
            response.raise_for_status()
            return await response.json()

        except ClientResponseError as err:
            if err.status == 401:
                _LOGGER.error("Authentication error: %s", err)
                raise TidalAuthError(f"Authentication error: {err}") from err
            _LOGGER.error("API request failed: %s", err)
            raise TidalConnectionError(f"API request failed: {err}") from err
        except ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise TidalConnectionError(f"Connection error: {err}") from err

    async def get_current_user(self) -> dict[str, Any]:
        """Get current user information.

        Returns:
            User data including user ID

        Raises:
            TidalAuthError: If not authenticated
            TidalConnectionError: If request fails
        """
        response = await self._request("GET", "users/me")
        return response.get("data", {})

    async def get_user_playlists(self) -> list[dict[str, Any]]:
        """Get user's playlists.

        Returns:
            List of playlist data
        """
        params = {"include": "playlists"}
        response = await self._request(
            "GET",
            f"userCollections/{self._user_id}/relationships/playlists",
            params=params,
        )
        return response.get("data", [])

    async def get_user_albums(self) -> list[dict[str, Any]]:
        """Get user's favorite albums.

        Returns:
            List of album data
        """
        params = {"include": "albums"}
        response = await self._request(
            "GET",
            f"userCollections/{self._user_id}/relationships/albums",
            params=params,
        )
        return response.get("data", [])

    async def get_user_tracks(self) -> list[dict[str, Any]]:
        """Get user's favorite tracks.

        Returns:
            List of track data
        """
        params = {"include": "tracks"}
        response = await self._request(
            "GET",
            f"userCollections/{self._user_id}/relationships/tracks",
            params=params,
        )
        return response.get("data", [])

    async def get_user_artists(self) -> list[dict[str, Any]]:
        """Get user's favorite artists.

        Returns:
            List of artist data
        """
        params = {"include": "artists"}
        response = await self._request(
            "GET",
            f"userCollections/{self._user_id}/relationships/artists",
            params=params,
        )
        return response.get("data", [])

    async def get_album(self, album_id: str) -> dict[str, Any]:
        """Get album details.

        Args:
            album_id: Album ID

        Returns:
            Album data
        """
        response = await self._request("GET", f"albums/{album_id}")
        return response.get("data", {})

    async def get_track(self, track_id: str) -> dict[str, Any]:
        """Get track details.

        Args:
            track_id: Track ID

        Returns:
            Track data
        """
        response = await self._request("GET", f"tracks/{track_id}")
        return response.get("data", {})

    async def get_playlist(self, playlist_id: str) -> dict[str, Any]:
        """Get playlist details.

        Args:
            playlist_id: Playlist ID

        Returns:
            Playlist data
        """
        response = await self._request("GET", f"playlists/{playlist_id}")
        return response.get("data", {})

    async def get_artist(self, artist_id: str) -> dict[str, Any]:
        """Get artist details.

        Args:
            artist_id: Artist ID

        Returns:
            Artist data
        """
        response = await self._request("GET", f"artists/{artist_id}")
        return response.get("data", {})

    async def search(
        self, query: str, search_type: str | None = None
    ) -> dict[str, Any]:
        """Search for content.

        Args:
            query: Search query
            search_type: Type of content to search (albums, tracks, playlists, artists)

        Returns:
            Search results
        """
        params = {"query": query}
        if search_type:
            params["type"] = search_type

        response = await self._request("GET", "searchResults", params=params)
        return response.get("data", {})

    async def create_playlist(self, name: str, description: str = "") -> dict[str, Any]:
        """Create a new playlist.

        Args:
            name: Playlist name
            description: Playlist description

        Returns:
            Created playlist data
        """
        data = {
            "data": {
                "type": "playlists",
                "attributes": {
                    "name": name,
                    "description": description,
                },
            }
        }

        response = await self._request(
            "POST",
            f"userCollections/{self._user_id}/relationships/playlists",
            json=data,
        )
        return response.get("data", {})

    async def add_to_playlist(self, playlist_id: str, track_ids: list[str]) -> None:
        """Add tracks to a playlist.

        Args:
            playlist_id: Playlist ID
            track_ids: List of track IDs to add
        """
        data = {
            "data": [
                {
                    "type": "tracks",
                    "id": track_id,
                }
                for track_id in track_ids
            ]
        }

        await self._request(
            "POST",
            f"playlists/{playlist_id}/relationships/tracks",
            json=data,
        )

    async def remove_from_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> None:
        """Remove tracks from a playlist.

        Args:
            playlist_id: Playlist ID
            track_ids: List of track IDs to remove
        """
        for track_id in track_ids:
            await self._request(
                "DELETE",
                f"playlists/{playlist_id}/relationships/tracks/{track_id}",
            )

    async def add_favorite_album(self, album_id: str) -> None:
        """Add album to favorites.

        Args:
            album_id: Album ID
        """
        data = {
            "data": {
                "type": "albums",
                "id": album_id,
            }
        }

        await self._request(
            "POST",
            f"userCollections/{self._user_id}/relationships/albums",
            json=data,
        )

    async def remove_favorite_album(self, album_id: str) -> None:
        """Remove album from favorites.

        Args:
            album_id: Album ID
        """
        await self._request(
            "DELETE",
            f"userCollections/{self._user_id}/relationships/albums/{album_id}",
        )

    async def add_favorite_track(self, track_id: str) -> None:
        """Add track to favorites.

        Args:
            track_id: Track ID
        """
        data = {
            "data": {
                "type": "tracks",
                "id": track_id,
            }
        }

        await self._request(
            "POST",
            f"userCollections/{self._user_id}/relationships/tracks",
            json=data,
        )

    async def remove_favorite_track(self, track_id: str) -> None:
        """Remove track from favorites.

        Args:
            track_id: Track ID
        """
        await self._request(
            "DELETE",
            f"userCollections/{self._user_id}/relationships/tracks/{track_id}",
        )

    @property
    def is_authenticated(self) -> bool:
        """Return if client is authenticated."""
        return self._oauth_session is not None

    @property
    def user_id(self) -> str:
        """Return the user ID."""
        return self._user_id
