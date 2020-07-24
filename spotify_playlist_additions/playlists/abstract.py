from abc import ABC, abstractmethod
from spotipy import Spotify

class AbstractPlaylist(ABC):
    """An abstract class that a new playlist can inherit callback functions
    from. Each frame, any of these may be invoked if the required state is
    found.
    """

    def __init__(self, spotify_client: Spotify):
        """The most basic initializer that can be implemented. Any playlist
        implementation needs take in a Spotify client from spotipy

        Args:
            spotify_client: A client that can be used for making Spotify API
                calls.
        """

        self._spotify_client = spotify_client

    @property
    def scope(self) -> str:
        """The required scope of the playlist implementation. Should be a
        simple property in the child class. Defaults to no scope

        Returns:
            str: The scope of the playlist.
        """

        return ""

    @abstractmethod
    def handle_skipped_track(self, track: dict) -> None:
        """Called on each configured playlist when the main loop detects a
        skipped track.

        Args:
            track: The skipped track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in their API.
        """

    @abstractmethod
    def handle_fully_listened_track(self, track: dict) -> None
        """Called on each configured playlist when the main loop detects a
        fully listened track (to within a degree of uncertainty)

        Args:
            track: The fully listened track retrieved from the Spotify API.
                Retains the exact format that Spotify defines in thei API
        """