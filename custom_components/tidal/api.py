"""Tidal API Client."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientResponseError

from .const import (
    API_BASE_URL,
    API_TOKEN_URL,
    OAUTH_SCOPES,
)

_LOGGER = logging.getLogger(__name__)


class TidalAuthError(Exception):
    """Exception to indicate authentication failure."""


class TidalConnectionError(Exception):
    """Exception to indicate connection failure."""


class TidalAPI:
    """Tidal API Client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        user_id: str,
        country_code: str = "US",
    ) -> None:
        """Initialize the Tidal API client.

        Args:
            session: aiohttp client session
            client_id: Tidal API client ID
            client_secret: Tidal API client secret
            user_id: Tidal user ID
            country_code: ISO 3166-1 country code
        """
        self._session = session
        self._client_id = client_id
        self._client_secret = client_secret
        self._user_id = user_id
        self._country_code = country_code
        self._access_token: str | None = None
        self._token_expires: datetime | None = None
        self._refresh_token: str | None = None

    async def authenticate(self, access_token: str | None = None, refresh_token: str | None = None) -> None:
        """Authenticate with Tidal API.

        Args:
            access_token: Optional existing access token
            refresh_token: Optional existing refresh token

        Raises:
            TidalAuthError: If authentication fails
        """
        if access_token and refresh_token:
            self._access_token = access_token
            self._refresh_token = refresh_token
            # Assume token expires in 1 hour if not specified
            self._token_expires = datetime.now() + timedelta(hours=1)
        else:
            await self._get_client_credentials()

    async def _get_client_credentials(self) -> None:
        """Get access token using client credentials flow.

        Raises:
            TidalAuthError: If authentication fails
            TidalConnectionError: If connection fails
        """
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }

            async with self._session.post(API_TOKEN_URL, data=data) as response:
                response.raise_for_status()
                token_data = await response.json()

                self._access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires = datetime.now() + timedelta(seconds=expires_in)
                self._refresh_token = token_data.get("refresh_token")

                _LOGGER.info("Successfully authenticated with Tidal API")

        except ClientResponseError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise TidalAuthError(f"Authentication failed: {err}") from err
        except ClientError as err:
            _LOGGER.error("Connection error during authentication: %s", err)
            raise TidalConnectionError(f"Connection error: {err}") from err

    async def _ensure_token_valid(self) -> None:
        """Ensure the access token is valid, refresh if needed.

        Raises:
            TidalAuthError: If token refresh fails
        """
        if not self._access_token or not self._token_expires:
            await self._get_client_credentials()
            return

        # Refresh token if it expires in less than 5 minutes
        if datetime.now() >= self._token_expires - timedelta(minutes=5):
            if self._refresh_token:
                await self._refresh_access_token()
            else:
                await self._get_client_credentials()

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using refresh token.

        Raises:
            TidalAuthError: If token refresh fails
            TidalConnectionError: If connection fails
        """
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }

            async with self._session.post(API_TOKEN_URL, data=data) as response:
                response.raise_for_status()
                token_data = await response.json()

                self._access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires = datetime.now() + timedelta(seconds=expires_in)
                self._refresh_token = token_data.get("refresh_token", self._refresh_token)

                _LOGGER.debug("Successfully refreshed access token")

        except ClientResponseError as err:
            _LOGGER.error("Token refresh failed: %s", err)
            raise TidalAuthError(f"Token refresh failed: {err}") from err
        except ClientError as err:
            _LOGGER.error("Connection error during token refresh: %s", err)
            raise TidalConnectionError(f"Connection error: {err}") from err

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
        await self._ensure_token_valid()

        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/vnd.api+json",
        }

        # Add country code to params if not already present
        params = kwargs.get("params", {})
        if "countryCode" not in params:
            params["countryCode"] = self._country_code
        kwargs["params"] = params

        try:
            async with self._session.request(method, url, headers=headers, **kwargs) as response:
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

    async def get_user_playlists(self) -> list[dict[str, Any]]:
        """Get user's playlists.

        Returns:
            List of playlist data
        """
        response = await self._request("GET", f"userCollections/{self._user_id}/playlists")
        return response.get("data", [])

    async def get_user_albums(self) -> list[dict[str, Any]]:
        """Get user's favorite albums.

        Returns:
            List of album data
        """
        response = await self._request("GET", f"userCollections/{self._user_id}/albums")
        return response.get("data", [])

    async def get_user_tracks(self) -> list[dict[str, Any]]:
        """Get user's favorite tracks.

        Returns:
            List of track data
        """
        response = await self._request("GET", f"userCollections/{self._user_id}/tracks")
        return response.get("data", [])

    async def get_user_artists(self) -> list[dict[str, Any]]:
        """Get user's favorite artists.

        Returns:
            List of artist data
        """
        response = await self._request("GET", f"userCollections/{self._user_id}/artists")
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

    async def search(self, query: str, search_type: str | None = None) -> dict[str, Any]:
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
            f"userCollections/{self._user_id}/playlists",
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
            f"playlists/{playlist_id}/tracks",
            json=data,
        )

    async def remove_from_playlist(self, playlist_id: str, track_ids: list[str]) -> None:
        """Remove tracks from a playlist.

        Args:
            playlist_id: Playlist ID
            track_ids: List of track IDs to remove
        """
        for track_id in track_ids:
            await self._request(
                "DELETE",
                f"playlists/{playlist_id}/tracks/{track_id}",
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
            f"userCollections/{self._user_id}/albums",
            json=data,
        )

    async def remove_favorite_album(self, album_id: str) -> None:
        """Remove album from favorites.

        Args:
            album_id: Album ID
        """
        await self._request(
            "DELETE",
            f"userCollections/{self._user_id}/albums/{album_id}",
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
            f"userCollections/{self._user_id}/tracks",
            json=data,
        )

    async def remove_favorite_track(self, track_id: str) -> None:
        """Remove track from favorites.

        Args:
            track_id: Track ID
        """
        await self._request(
            "DELETE",
            f"userCollections/{self._user_id}/tracks/{track_id}",
        )

    @property
    def is_authenticated(self) -> bool:
        """Return if client is authenticated."""
        return self._access_token is not None

    @property
    def user_id(self) -> str:
        """Return the user ID."""
        return self._user_id
