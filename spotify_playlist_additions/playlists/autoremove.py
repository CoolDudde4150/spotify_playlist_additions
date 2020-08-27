"""
Contains a child class of an AbstractPlaylist that implements functionality for automatically removing songs that
were detected to be skipped
"""

import logging
from typing import Any

from spotify_playlist_additions.playlists.abstract import AbstractPlaylist

LOG = logging.getLogger(__name__)


class AutoRemovePlaylist(AbstractPlaylist):
    """A playlist addon that removes songs that were detected to be skipped.
    """

    scope = "user-read-currently-playing playlist-modify-public"

    async def start(self) -> Any:
        """Method called at the start of runtime. Only called once.
        """
        pass

    async def stop(self) -> Any:
        """Method called at the end of runtime. Only called once
        """
        pass

    async def handle_skipped_track(self, track: dict) -> Any:
        """
        Removes the track from the given playlist

        Args:
            track: The skipped track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API.
        """

        LOG.info("Removing %s from playlist", track["item"]["name"])
        self._spotify_client.user_playlist_remove_all_occurrences_of_tracks(
            self._user_id, self._playlist["id"], [track["item"]["id"]])

    async def handle_fully_listened_track(self, track: dict) -> Any:
        """Called on each configured playlist when the main loop detects a
        fully listened track (to within a degree of uncertainty)

        Args:
            track: The fully listened track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API
        """

        pass
