"""LLM Tools for Tidal integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType

from .const import DOMAIN
from .coordinator import TidalDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class GetPlaylistsTool(llm.Tool):
    """Tool to get user's Tidal playlists."""

    name = "tidal_get_playlists"
    description = "Get the user's Tidal playlists with their IDs, names, and descriptions"

    def __init__(self, coordinator: TidalDataUpdateCoordinator) -> None:
        """Initialize the tool."""
        self.coordinator = coordinator

    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> JsonObjectType:
        """Get user playlists."""
        playlists = self.coordinator.playlists
        result = []

        for playlist in playlists:
            attributes = playlist.get("attributes", {})
            result.append(
                {
                    "id": playlist.get("id"),
                    "name": attributes.get("name", "Unknown"),
                    "description": attributes.get("description", ""),
                }
            )

        return {
            "playlists": result,
            "count": len(result),
        }


class GetAlbumsTool(llm.Tool):
    """Tool to get user's favorite Tidal albums."""

    name = "tidal_get_albums"
    description = "Get the user's favorite Tidal albums with their IDs, titles, and barcodes"

    def __init__(self, coordinator: TidalDataUpdateCoordinator) -> None:
        """Initialize the tool."""
        self.coordinator = coordinator

    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> JsonObjectType:
        """Get user albums."""
        albums = self.coordinator.albums
        result = []

        for album in albums:
            attributes = album.get("attributes", {})
            result.append(
                {
                    "id": album.get("id"),
                    "title": attributes.get("title", "Unknown"),
                    "barcode": attributes.get("barcode", ""),
                }
            )

        return {
            "albums": result,
            "count": len(result),
        }


class GetTracksTool(llm.Tool):
    """Tool to get user's favorite Tidal tracks."""

    name = "tidal_get_tracks"
    description = "Get the user's favorite Tidal tracks with their IDs, titles, and ISRC codes"

    def __init__(self, coordinator: TidalDataUpdateCoordinator) -> None:
        """Initialize the tool."""
        self.coordinator = coordinator

    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> JsonObjectType:
        """Get user tracks."""
        tracks = self.coordinator.tracks
        result = []

        for track in tracks:
            attributes = track.get("attributes", {})
            result.append(
                {
                    "id": track.get("id"),
                    "title": attributes.get("title", "Unknown"),
                    "isrc": attributes.get("isrc", ""),
                }
            )

        return {
            "tracks": result,
            "count": len(result),
        }


class GetArtistsTool(llm.Tool):
    """Tool to get user's favorite Tidal artists."""

    name = "tidal_get_artists"
    description = "Get the user's favorite Tidal artists with their IDs and names"

    def __init__(self, coordinator: TidalDataUpdateCoordinator) -> None:
        """Initialize the tool."""
        self.coordinator = coordinator

    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> JsonObjectType:
        """Get user artists."""
        artists = self.coordinator.artists
        result = []

        for artist in artists:
            attributes = artist.get("attributes", {})
            result.append(
                {
                    "id": artist.get("id"),
                    "name": attributes.get("name", "Unknown"),
                }
            )

        return {
            "artists": result,
            "count": len(result),
        }


class SearchContentTool(llm.Tool):
    """Tool to search for content on Tidal."""

    name = "tidal_search"
    description = "Search for content on Tidal (albums, tracks, playlists, artists)"

    parameters = vol.Schema(
        {
            vol.Required("query"): str,
            vol.Optional("type"): str,
        }
    )

    def __init__(self, coordinator: TidalDataUpdateCoordinator) -> None:
        """Initialize the tool."""
        self.coordinator = coordinator

    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> JsonObjectType:
        """Search for content."""
        query = tool_input.tool_args.get("query", "")
        search_type = tool_input.tool_args.get("type")

        if not query:
            raise HomeAssistantError("Search query is required")

        try:
            results = await self.coordinator.async_search(query, search_type)
            return {"results": results}
        except Exception as err:
            _LOGGER.error("Error searching: %s", err)
            raise HomeAssistantError(f"Error searching: {err}") from err


class PlayContentTool(llm.Tool):
    """Tool to play content on Tidal."""

    name = "tidal_play_content"
    description = "Play content on Tidal (track, album, playlist, artist)"

    parameters = vol.Schema(
        {
            vol.Required("content_type"): str,
            vol.Required("content_id"): str,
            vol.Optional("entity_id"): str,
        }
    )

    def __init__(self, coordinator: TidalDataUpdateCoordinator) -> None:
        """Initialize the tool."""
        self.coordinator = coordinator

    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ) -> JsonObjectType:
        """Play content."""
        content_type = tool_input.tool_args.get("content_type", "")
        content_id = tool_input.tool_args.get("content_id", "")
        entity_id = tool_input.tool_args.get("entity_id")

        if not content_type or not content_id:
            raise HomeAssistantError("Content type and ID are required")

        try:
            service_data = {
                f"{content_type}_id": content_id,
            }
            if entity_id:
                service_data["entity_id"] = entity_id

            service_name = f"play_{content_type}"
            await hass.services.async_call(DOMAIN, service_name, service_data)

            return {
                "status": "success",
                "message": f"Playing {content_type} {content_id}",
            }
        except Exception as err:
            _LOGGER.error("Error playing content: %s", err)
            raise HomeAssistantError(f"Error playing content: {err}") from err


class TidalAPI(llm.API):
    """Tidal LLM API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: TidalDataUpdateCoordinator,
    ) -> None:
        """Initialize the API."""
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        super().__init__(
            hass=hass,
            id=f"{DOMAIN}-{entry.entry_id}",
            name=f"Tidal ({entry.title})",
        )

    async def async_get_api_instance(
        self, llm_context: llm.LLMContext
    ) -> llm.APIInstance:
        """Return the API instance."""
        return llm.APIInstance(
            api=self,
            api_prompt=(
                "You can use these tools to interact with the user's Tidal account. "
                "You can get their playlists, favorite albums, tracks, and artists. "
                "You can also search for content and play content on Tidal."
            ),
            llm_context=llm_context,
            tools=[
                GetPlaylistsTool(self.coordinator),
                GetAlbumsTool(self.coordinator),
                GetTracksTool(self.coordinator),
                GetArtistsTool(self.coordinator),
                SearchContentTool(self.coordinator),
                PlayContentTool(self.coordinator),
            ],
        )


async def async_setup_llm_tools(
    hass: HomeAssistant, entry: ConfigEntry
) -> callable:
    """Set up LLM tools for Tidal.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        Unregister function
    """
    coordinator = entry.runtime_data

    # Create and register the API
    api = TidalAPI(hass, entry, coordinator)
    unreg = llm.async_register_api(hass, api)

    _LOGGER.debug("LLM API registered for Tidal")

    return unreg
