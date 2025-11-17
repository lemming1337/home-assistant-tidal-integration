"""LLM Tools for Tidal integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    TOOL_GET_ALBUMS,
    TOOL_GET_ARTISTS,
    TOOL_GET_PLAYLISTS,
    TOOL_GET_TRACKS,
    TOOL_PLAY_CONTENT,
    TOOL_SEARCH,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_llm_tools(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up LLM tools for Tidal.

    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    coordinator = entry.runtime_data

    # Create LLM API
    api = llm.async_register_api(hass, coordinator.api)

    # Register tools
    @api.register_tool
    async def get_playlists(
        tool_input: llm.ToolInput,
    ) -> dict[str, Any]:
        """Get user's Tidal playlists.

        Returns a list of the user's playlists with their IDs, names, and descriptions.
        """
        playlists = coordinator.playlists
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

    @api.register_tool
    async def get_albums(
        tool_input: llm.ToolInput,
    ) -> dict[str, Any]:
        """Get user's favorite Tidal albums.

        Returns a list of the user's favorite albums with their IDs, titles, and barcodes.
        """
        albums = coordinator.albums
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

    @api.register_tool
    async def get_tracks(
        tool_input: llm.ToolInput,
    ) -> dict[str, Any]:
        """Get user's favorite Tidal tracks.

        Returns a list of the user's favorite tracks with their IDs, titles, and ISRC codes.
        """
        tracks = coordinator.tracks
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

    @api.register_tool
    async def get_artists(
        tool_input: llm.ToolInput,
    ) -> dict[str, Any]:
        """Get user's favorite Tidal artists.

        Returns a list of the user's favorite artists with their IDs and names.
        """
        artists = coordinator.artists
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

    @api.register_tool(
        llm.ToolInput(
            tool_name=TOOL_SEARCH,
            tool_args=[
                llm.ToolArgument(
                    name="query",
                    description="Search query",
                    type="string",
                    required=True,
                ),
                llm.ToolArgument(
                    name="type",
                    description="Type of content to search for (albums, tracks, playlists, artists)",
                    type="string",
                    required=False,
                ),
            ],
        )
    )
    async def search_content(
        tool_input: llm.ToolInput,
    ) -> dict[str, Any]:
        """Search for content on Tidal.

        Args:
            query: Search query
            type: Type of content to search (optional)

        Returns a list of search results.
        """
        query = tool_input.arguments.get("query", "")
        search_type = tool_input.arguments.get("type")

        if not query:
            return {
                "error": "Search query is required",
            }

        try:
            results = await coordinator.async_search(query, search_type)
            return {
                "results": results,
            }
        except Exception as err:
            _LOGGER.error("Error searching: %s", err)
            return {
                "error": str(err),
            }

    @api.register_tool(
        llm.ToolInput(
            tool_name=TOOL_PLAY_CONTENT,
            tool_description="Play content on Tidal",
            tool_args=[
                llm.ToolArgument(
                    name="content_type",
                    description="Type of content (track, album, playlist, artist)",
                    type="string",
                    required=True,
                ),
                llm.ToolArgument(
                    name="content_id",
                    description="ID of the content to play",
                    type="string",
                    required=True,
                ),
                llm.ToolArgument(
                    name="entity_id",
                    description="Entity ID of the media player (optional)",
                    type="string",
                    required=False,
                ),
            ],
        )
    )
    async def play_content(
        tool_input: llm.ToolInput,
    ) -> dict[str, Any]:
        """Play content on Tidal.

        Args:
            content_type: Type of content (track, album, playlist, artist)
            content_id: ID of the content
            entity_id: Entity ID of the media player (optional)

        Returns a status message.
        """
        content_type = tool_input.arguments.get("content_type", "")
        content_id = tool_input.arguments.get("content_id", "")
        entity_id = tool_input.arguments.get("entity_id")

        if not content_type or not content_id:
            return {
                "error": "Content type and ID are required",
            }

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
            return {
                "error": str(err),
            }

    # Register the API
    llm.async_register_api(hass, api)

    _LOGGER.debug("LLM tools registered for Tidal")
