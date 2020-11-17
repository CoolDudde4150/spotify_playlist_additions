"""
Contains the child of an abstract playlist addon for an automatic song adding playlist when a song is fully listened.
"""

import logging
from typing import Any

from async_spotify.api.spotify_api_client import SpotifyApiClient

from spotify_playlist_additions.playlists.abstract import AbstractPlaylist

LOG = logging.getLogger(__name__)


class AutoAddPlaylist(AbstractPlaylist):
    """A playlist addon that is intended to automatically add songs that are fully listened to the given playlist"""

    scope = "user-read-currently-playing playlist-modify-public"

    async def start(self) -> Any:
        """Method called at the start of runtime. Only called once.
        """

        pass

    async def stop(self) -> Any:
        """Method called at the end of runtime. Only called once
        """

        pass

    async def handle_skipped_track(self, track: dict, spotify_client: SpotifyApiClient):
        """Called on each configured playlist when the main loop detects a
        fully listened track (to within a degree of uncertainty)

        Args:
            track: The fully listened track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API
        """
        pass

    async def handle_fully_listened_track(self, track: dict, spotify_client: SpotifyApiClient):
        """Ensures that the playlist doesnt contain the track, then adds it to the playlist

        Args:
            track: The skipped track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API.
        """

        if not self._playlist_contains_track(track, spotify_client):
            LOG.info("Added %s to playlist", track["item"]["name"])
            spotify_client.playlists.add_tracks(self._playlist["id"], [track["item"]["id"]])

    async def _playlist_contains_track(self, track: dict, spotify_client: SpotifyApiClient) -> bool:
        """
        Searches the playlist in O(n) time for the track name.

        Args:
            track: The track that is being looked for. In the format of a spotify API track.

        Returns:
            bool: Whether the playlist contains the track.
        """

        # TODO: There is almost certainly a better way to do this. It would be best to have this calculated only once
        # instead of every playlist addon doing it.
        
        LOG.info("Performing a search for %s", track["item"]["name"])

        length = 100
        offset = 0
        while length == 100:
            playlist_tracks = await spotify_client.playlists.get_tracks(
                self._playlist["id"],
                fields="items(track(name))",
                offset=offset)
            for playlist_track in playlist_tracks["items"]:
                if playlist_track["track"]["name"] == track["item"]["name"]:
                    LOG.info("Playlist already contains %s",
                             track["item"]["name"])
                    return True

            length = len(playlist_tracks["items"])
            offset += length

        LOG.info("Did not find %s in playlist. Adding", track["item"]["name"])

        return False
