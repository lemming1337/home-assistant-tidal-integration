"""Support for Tidal media player."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TidalDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tidal media player from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: TidalDataUpdateCoordinator = entry.runtime_data

    async_add_entities([TidalMediaPlayer(coordinator, entry)])


class TidalMediaPlayer(MediaPlayerEntity):
    """Representation of a Tidal media player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_media_content_type = MediaType.MUSIC

    def __init__(
        self,
        coordinator: TidalDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the Tidal media player.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Tidal {coordinator.api.user_id}",
            "manufacturer": "Tidal",
            "model": "Tidal Music",
        }

        # Current playback state
        self._state = MediaPlayerState.IDLE
        self._current_track: dict[str, Any] | None = None
        self._current_playlist: dict[str, Any] | None = None
        self._current_album: dict[str, Any] | None = None
        self._volume_level: float = 1.0
        self._is_muted: bool = False

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return (
            MediaPlayerEntityFeature.BROWSE_MEDIA
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.PLAY_MEDIA
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        return self._state

    @property
    def volume_level(self) -> float:
        """Volume level of the media player (0..1)."""
        return self._volume_level

    @property
    def is_volume_muted(self) -> bool:
        """Boolean if volume is currently muted."""
        return self._is_muted

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        if self._current_track:
            attributes = self._current_track.get("attributes", {})
            return attributes.get("title")
        return None

    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media."""
        if self._current_track:
            # Try to get artist from relationships
            if "relationships" in self._current_track:
                artists = self._current_track["relationships"].get("artists", {}).get("data", [])
                if artists:
                    return artists[0].get("attributes", {}).get("name")
        return None

    @property
    def media_album_name(self) -> str | None:
        """Album name of current playing media."""
        if self._current_album:
            attributes = self._current_album.get("attributes", {})
            return attributes.get("title")
        return None

    @property
    def media_image_url(self) -> str | None:
        """Image url of current playing media."""
        # Try to get cover art from current track or album
        source = self._current_track or self._current_album
        if source and "relationships" in source:
            covers = source["relationships"].get("coverArt", {}).get("data", [])
            if covers:
                cover_attributes = covers[0].get("attributes", {})
                # Prefer high resolution image
                for size in ["xxl", "xl", "l", "m", "s"]:
                    url = cover_attributes.get(f"url{size.upper()}")
                    if url:
                        return url
        return None

    async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media.

        Args:
            media_type: Type of media
            media_id: Media ID
            **kwargs: Additional arguments
        """
        _LOGGER.debug("Playing media: type=%s, id=%s", media_type, media_id)

        try:
            if media_type == MediaType.TRACK:
                track = await self._coordinator.api.get_track(media_id)
                self._current_track = track
                self._state = MediaPlayerState.PLAYING

            elif media_type == MediaType.PLAYLIST:
                playlist = await self._coordinator.api.get_playlist(media_id)
                self._current_playlist = playlist
                # Get first track from playlist
                tracks = await self._coordinator.async_get_playlist_tracks(media_id)
                if tracks:
                    self._current_track = tracks[0]
                self._state = MediaPlayerState.PLAYING

            elif media_type == MediaType.ALBUM:
                album = await self._coordinator.api.get_album(media_id)
                self._current_album = album
                # Get first track from album
                tracks = await self._coordinator.async_get_album_tracks(media_id)
                if tracks:
                    self._current_track = tracks[0]
                self._state = MediaPlayerState.PLAYING

            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Error playing media: %s", err)

    async def async_media_play(self) -> None:
        """Send play command."""
        self._state = MediaPlayerState.PLAYING
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        self._state = MediaPlayerState.PAUSED
        self.async_write_ha_state()

    async def async_media_stop(self) -> None:
        """Send stop command."""
        self._state = MediaPlayerState.IDLE
        self._current_track = None
        self._current_playlist = None
        self._current_album = None
        self.async_write_ha_state()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        # This is a placeholder - in a real implementation,
        # you would get the next track from the current playlist/album
        _LOGGER.debug("Next track requested")
        self.async_write_ha_state()

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        # This is a placeholder - in a real implementation,
        # you would get the previous track from the current playlist/album
        _LOGGER.debug("Previous track requested")
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1.

        Args:
            volume: Volume level
        """
        self._volume_level = volume
        self.async_write_ha_state()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume.

        Args:
            mute: Mute state
        """
        self._is_muted = mute
        self.async_write_ha_state()

    async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper.

        Args:
            media_content_type: Type of media to browse
            media_content_id: Media ID to browse

        Returns:
            BrowseMedia object
        """
        return await self._async_browse_media(media_content_type, media_content_id)

    async def _async_browse_media(
        self,
        media_content_type: MediaType | str | None,
        media_content_id: str | None,
    ) -> BrowseMedia:
        """Browse media.

        Args:
            media_content_type: Type of media to browse
            media_content_id: Media ID to browse

        Returns:
            BrowseMedia object
        """
        if media_content_id is None:
            # Root level - show main categories
            return BrowseMedia(
                media_class=MediaType.CHANNEL,
                media_content_id="root",
                media_content_type="root",
                title="Tidal",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(
                        media_class=MediaType.PLAYLIST,
                        media_content_id="playlists",
                        media_content_type="playlists",
                        title="Playlists",
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        media_class=MediaType.ALBUM,
                        media_content_id="albums",
                        media_content_type="albums",
                        title="Albums",
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        media_class=MediaType.TRACK,
                        media_content_id="tracks",
                        media_content_type="tracks",
                        title="Tracks",
                        can_play=False,
                        can_expand=True,
                    ),
                ],
            )

        # Browse specific categories
        if media_content_id == "playlists":
            playlists = self._coordinator.playlists
            children = []
            for playlist in playlists:
                attributes = playlist.get("attributes", {})
                children.append(
                    BrowseMedia(
                        media_class=MediaType.PLAYLIST,
                        media_content_id=playlist["id"],
                        media_content_type=MediaType.PLAYLIST,
                        title=attributes.get("name", "Unknown"),
                        can_play=True,
                        can_expand=False,
                    )
                )

            return BrowseMedia(
                media_class=MediaType.PLAYLIST,
                media_content_id="playlists",
                media_content_type="playlists",
                title="Playlists",
                can_play=False,
                can_expand=True,
                children=children,
            )

        elif media_content_id == "albums":
            albums = self._coordinator.albums
            children = []
            for album in albums:
                attributes = album.get("attributes", {})
                children.append(
                    BrowseMedia(
                        media_class=MediaType.ALBUM,
                        media_content_id=album["id"],
                        media_content_type=MediaType.ALBUM,
                        title=attributes.get("title", "Unknown"),
                        can_play=True,
                        can_expand=False,
                    )
                )

            return BrowseMedia(
                media_class=MediaType.ALBUM,
                media_content_id="albums",
                media_content_type="albums",
                title="Albums",
                can_play=False,
                can_expand=True,
                children=children,
            )

        elif media_content_id == "tracks":
            tracks = self._coordinator.tracks
            children = []
            for track in tracks:
                attributes = track.get("attributes", {})
                children.append(
                    BrowseMedia(
                        media_class=MediaType.TRACK,
                        media_content_id=track["id"],
                        media_content_type=MediaType.TRACK,
                        title=attributes.get("title", "Unknown"),
                        can_play=True,
                        can_expand=False,
                    )
                )

            return BrowseMedia(
                media_class=MediaType.TRACK,
                media_content_id="tracks",
                media_content_type="tracks",
                title="Tracks",
                can_play=False,
                can_expand=True,
                children=children,
            )

        # Default fallback
        return BrowseMedia(
            media_class=MediaType.CHANNEL,
            media_content_id="root",
            media_content_type="root",
            title="Tidal",
            can_play=False,
            can_expand=True,
        )
