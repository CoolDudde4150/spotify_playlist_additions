"""Contains the abstract interface for a playlist addon."""

from abc import ABC, abstractmethod
from typing import Any
from async_spotify import SpotifyApiClient


class AbstractPlaylist(ABC):
    """An abstract class that a new playlist can inherit callback functions from.

    Each frame, any of these may be invoked if the required state is found.
    """
    def __init__(self, playlist: dict, user_id: str):
        """The most basic initializer that can be implemented.

        Any playlist implementation needs take in a Spotify client from spotipy and a playlist

        Args:
            spotify_client: A client that can be used for making Spotify API
                calls.
            playlist: The playlist that this runtime has been configured to run on. In the same format as described on
                the spotify API
            user_id: The user ID that has connected to this runtime.
        """
        self._playlist = playlist
        self._user_id = user_id

    @property
    def scope(self) -> str:
        """The required scope of the playlist addon.

        Should be a class variable called scope, equal to a string.

        See https://developer.spotify.com/documentation/general/guides/scopes/.

        Returns:
            str: The scope of the playlist. Defaults to "" (no scope)
        """
        return ""

    @abstractmethod
    async def start(self):
        """Method called at the start of runtime. Only called once."""

    @abstractmethod
    async def stop(self):
        """Method called at the end of runtime. Only called once."""

    @abstractmethod
    async def handle_skipped_track(self, track: dict,
                                   spotify_client: SpotifyApiClient) -> Any:
        """Called when a track is detected as skipped.

        Args:
            track: The skipped track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API.
            spotify_client: A client that can be used to make spotify requests
        """

    @abstractmethod
    async def handle_fully_listened_track(
            self, track: dict, spotify_client: SpotifyApiClient) -> Any:
        """Called when a track is detected as fully listened.

        Args:
            track: The fully listened track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API
            spotify_client: A client that can be used to make spotify requests
        """
