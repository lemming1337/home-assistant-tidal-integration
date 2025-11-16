# Tidal Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Home Assistant integration for Tidal music streaming service, providing media player functionality, statistics sensors, and LLM tools for AI assistants.

## Features

- **Media Player Entity**: Full-featured media player for Tidal with browsing capabilities
- **Sensor Entities**: Track your favorite playlists, albums, tracks, and artists
- **Services**: Rich set of services for controlling Tidal playback and managing playlists
- **LLM Tools**: Integration with Home Assistant's conversation agents for AI-powered music control
- **Media Browsing**: Browse your Tidal library directly in Home Assistant
- **HACS Support**: Easy installation via Home Assistant Community Store

## Prerequisites

Before installing this integration, you need:

1. A Tidal account (Premium recommended for full playback control)
2. Tidal API credentials:
   - Client ID
   - Client Secret
   - User ID

### Getting Tidal API Credentials

1. Visit the [Tidal Developer Portal](https://developer.tidal.com/)
2. Sign in with your Tidal account
3. Create a new application
4. Note down your Client ID and Client Secret
5. Find your User ID in your Tidal account settings

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/lemming1337/home-assistant-tidal-integration`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Tidal" in the integration list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/tidal` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Tidal"
4. Enter your credentials:
   - Client ID
   - Client Secret
   - User ID
   - Country Code (optional, defaults to "US")
5. Click "Submit"

## Entities

### Media Player

- **Entity ID**: `media_player.tidal_{user_id}`
- **Features**:
  - Play/Pause/Stop
  - Next/Previous track
  - Volume control
  - Media browsing
  - Play media from URL or ID

### Sensors

#### Playlists Sensor
- **Entity ID**: `sensor.tidal_{user_id}_playlists`
- **State**: Number of playlists
- **Attributes**: List of playlists with IDs, names, and descriptions

#### Favorite Albums Sensor
- **Entity ID**: `sensor.tidal_{user_id}_favorite_albums`
- **State**: Number of favorite albums
- **Attributes**: List of albums with IDs, titles, and barcodes

#### Favorite Tracks Sensor
- **Entity ID**: `sensor.tidal_{user_id}_favorite_tracks`
- **State**: Number of favorite tracks
- **Attributes**: List of tracks with IDs, titles, and ISRC codes

#### Favorite Artists Sensor
- **Entity ID**: `sensor.tidal_{user_id}_favorite_artists`
- **State**: Number of favorite artists
- **Attributes**: List of artists with IDs and names

## Services

### `tidal.play_playlist`
Play a Tidal playlist.

```yaml
service: tidal.play_playlist
data:
  playlist_id: "36ea71a8-445e-41a4-82ab-6628c581535d"
  entity_id: media_player.tidal
```

### `tidal.play_album`
Play a Tidal album.

```yaml
service: tidal.play_album
data:
  album_id: "251380836"
  entity_id: media_player.tidal
```

### `tidal.play_track`
Play a Tidal track.

```yaml
service: tidal.play_track
data:
  track_id: "251380837"
  entity_id: media_player.tidal
```

### `tidal.play_artist`
Play music from a Tidal artist.

```yaml
service: tidal.play_artist
data:
  artist_id: "3503597"
  entity_id: media_player.tidal
```

### `tidal.create_playlist`
Create a new Tidal playlist.

```yaml
service: tidal.create_playlist
data:
  name: "My New Playlist"
  description: "A playlist created from Home Assistant"
```

### `tidal.add_to_playlist`
Add tracks to a playlist.

```yaml
service: tidal.add_to_playlist
data:
  playlist_id: "36ea71a8-445e-41a4-82ab-6628c581535d"
  track_ids:
    - "251380837"
    - "251380838"
```

### `tidal.remove_from_playlist`
Remove tracks from a playlist.

```yaml
service: tidal.remove_from_playlist
data:
  playlist_id: "36ea71a8-445e-41a4-82ab-6628c581535d"
  track_ids:
    - "251380837"
```

### `tidal.like_track`
Add a track to favorites.

```yaml
service: tidal.like_track
data:
  track_id: "251380837"
```

### `tidal.unlike_track`
Remove a track from favorites.

```yaml
service: tidal.unlike_track
data:
  track_id: "251380837"
```

## LLM Tools

This integration provides tools for Home Assistant's conversation agents (like Google Generative AI, OpenAI, or local LLMs):

- **Get Playlists**: Retrieve user's playlists
- **Get Albums**: Retrieve user's favorite albums
- **Get Tracks**: Retrieve user's favorite tracks
- **Get Artists**: Retrieve user's favorite artists
- **Search**: Search for content on Tidal
- **Play Content**: Play specific content on Tidal

### Example LLM Usage

With a configured conversation agent, you can say:

- "Show me my Tidal playlists"
- "Play my favorite Tidal album"
- "Search for artist on Tidal"
- "Add this track to my Tidal favorites"

## Automations

### Play Music Based on Time

```yaml
automation:
  - alias: "Morning Music"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: tidal.play_playlist
        data:
          playlist_id: "your-morning-playlist-id"
          entity_id: media_player.tidal
```

### Like Currently Playing Track

```yaml
automation:
  - alias: "Like Current Track"
    trigger:
      - platform: event
        event_type: custom_button_press
    action:
      - service: tidal.like_track
        data:
          track_id: "{{ state_attr('media_player.tidal', 'media_content_id') }}"
```

## Troubleshooting

### Authentication Issues

If you experience authentication problems:

1. Verify your Client ID and Client Secret are correct
2. Check that your User ID matches your Tidal account
3. Ensure your Tidal API application is in "Development" or "Production" mode
4. Try removing and re-adding the integration

### Connection Errors

If the integration cannot connect:

1. Check your internet connection
2. Verify Tidal services are operational
3. Review Home Assistant logs for specific error messages
4. Ensure your API credentials have not expired

### Data Not Updating

If sensors are not updating:

1. Check the integration status in Settings → Devices & Services
2. Review logs for update errors
3. Try reloading the integration
4. Verify your Tidal account has playlists/albums/tracks saved

## API Rate Limits

The Tidal API has rate limits. This integration:

- Updates data every 30 seconds by default
- Caches API responses to minimize requests
- Handles rate limit errors gracefully

## Privacy & Data

This integration:

- Communicates directly with Tidal's API
- Does not store your API credentials in plain text
- Does not send data to any third-party services
- Only accesses data you explicitly grant access to

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Support

- Report issues: [GitHub Issues](https://github.com/lemming1337/home-assistant-tidal-integration/issues)
- Feature requests: [GitHub Discussions](https://github.com/lemming1337/home-assistant-tidal-integration/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Tidal](https://tidal.com/) for providing the API
- [Home Assistant](https://www.home-assistant.io/) community
- All contributors to this project

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Tidal.
