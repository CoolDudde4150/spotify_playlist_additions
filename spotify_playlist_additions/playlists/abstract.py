from abc import ABC, abstractmethod
from typing import Any
from spotipy import Spotify


class AbstractPlaylist(ABC):
    """An abstract class that a new playlist can inherit callback functions
    from. Each frame, any of these may be invoked if the required state is
    found.
    """

    def __init__(self, spotify_client: Spotify, playlist: dict, user_id: str):
        """The most basic initializer that can be implemented. Any playlist
        implementation needs take in a Spotify client from spotipy and a playlist

        Args:
            spotify_client: A client that can be used for making Spotify API
                calls.
            playlist: The playlist that this runtime has been configured to run on. In the same format as described on
                the spotify API
            user_id: The user ID that has connected to this runtime.
        """

        self._spotify_client = spotify_client
        self._playlist = playlist
        self._user_id = user_id

    @property
    def scope(self) -> str:
        """The required scope of the playlist implementation. Should be a
        simple property in the child class. Defaults to no scope

        Returns:
            str: The scope of the playlist.
        """

        return ""

    @abstractmethod
    async def start(self) -> Any:
        """Method called at the start of runtime. Only called once.
        """

    @abstractmethod
    async def stop(self) -> Any:
        """Method called at the end of runtime. Only called once
        """

    @abstractmethod
    async def handle_skipped_track(self, track: dict) -> Any:
        """Called on each configured playlist when the main loop detects a
        skipped track.

        Args:
            track: The skipped track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API.
        """
    @abstractmethod
    async def handle_fully_listened_track(self, track: dict) -> Any:
        """Called on each configured playlist when the main loop detects a
        fully listened track (to within a degree of uncertainty)

        Args:
            track: The fully listened track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in thei API
        """
