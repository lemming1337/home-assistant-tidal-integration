"""Support for Tidal sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_FAVORITE_ALBUMS,
    SENSOR_FAVORITE_ARTISTS,
    SENSOR_FAVORITE_TRACKS,
    SENSOR_PLAYLISTS,
)
from .coordinator import TidalDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tidal sensors from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: TidalDataUpdateCoordinator = entry.runtime_data

    sensors = [
        TidalPlaylistsSensor(coordinator, entry),
        TidalFavoriteAlbumsSensor(coordinator, entry),
        TidalFavoriteTracksSensor(coordinator, entry),
        TidalFavoriteArtistsSensor(coordinator, entry),
    ]

    async_add_entities(sensors)


class TidalBaseSensor(CoordinatorEntity[TidalDataUpdateCoordinator], SensorEntity):
    """Base class for Tidal sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TidalDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        name: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
            sensor_type: Type of sensor
            name: Sensor name
        """
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Tidal {coordinator.api.user_id}",
            "manufacturer": "Tidal",
            "model": "Tidal Music",
        }


class TidalPlaylistsSensor(TidalBaseSensor):
    """Sensor for user playlists."""

    def __init__(
        self,
        coordinator: TidalDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the playlists sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator, entry, SENSOR_PLAYLISTS, "Playlists")
        self._attr_icon = "mdi:playlist-music"

    @property
    def native_value(self) -> int:
        """Return the number of playlists."""
        return len(self.coordinator.playlists)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        playlists = []
        for playlist in self.coordinator.playlists:
            attributes = playlist.get("attributes", {})
            playlists.append(
                {
                    "id": playlist.get("id"),
                    "name": attributes.get("name"),
                    "description": attributes.get("description"),
                }
            )

        return {
            "playlists": playlists,
        }


class TidalFavoriteAlbumsSensor(TidalBaseSensor):
    """Sensor for favorite albums."""

    def __init__(
        self,
        coordinator: TidalDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the favorite albums sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator, entry, SENSOR_FAVORITE_ALBUMS, "Favorite Albums")
        self._attr_icon = "mdi:album"

    @property
    def native_value(self) -> int:
        """Return the number of favorite albums."""
        return len(self.coordinator.albums)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        albums = []
        for album in self.coordinator.albums:
            attributes = album.get("attributes", {})
            albums.append(
                {
                    "id": album.get("id"),
                    "title": attributes.get("title"),
                    "barcode": attributes.get("barcode"),
                }
            )

        return {
            "albums": albums,
        }


class TidalFavoriteTracksSensor(TidalBaseSensor):
    """Sensor for favorite tracks."""

    def __init__(
        self,
        coordinator: TidalDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the favorite tracks sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator, entry, SENSOR_FAVORITE_TRACKS, "Favorite Tracks")
        self._attr_icon = "mdi:music-note"

    @property
    def native_value(self) -> int:
        """Return the number of favorite tracks."""
        return len(self.coordinator.tracks)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        tracks = []
        for track in self.coordinator.tracks:
            attributes = track.get("attributes", {})
            tracks.append(
                {
                    "id": track.get("id"),
                    "title": attributes.get("title"),
                    "isrc": attributes.get("isrc"),
                }
            )

        return {
            "tracks": tracks,
        }


class TidalFavoriteArtistsSensor(TidalBaseSensor):
    """Sensor for favorite artists."""

    def __init__(
        self,
        coordinator: TidalDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the favorite artists sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator, entry, SENSOR_FAVORITE_ARTISTS, "Favorite Artists")
        self._attr_icon = "mdi:account-music"

    @property
    def native_value(self) -> int:
        """Return the number of favorite artists."""
        return len(self.coordinator.artists)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        artists = []
        for artist in self.coordinator.artists:
            attributes = artist.get("attributes", {})
            artists.append(
                {
                    "id": artist.get("id"),
                    "name": attributes.get("name"),
                }
            )

        return {
            "artists": artists,
        }
