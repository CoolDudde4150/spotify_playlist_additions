"""Represents a single playlist being managed by the spotify engine."""

from async_spotify.api.spotify_api_client import SpotifyApiClient


class SpotifyPlaylist:
    """Represents a singular, managed playlist."""

    # def __init__(self, playlist: dict, user_id: str):
    #     self._playlist = playlist
    #     self._user_id = user_id
    async def handle_skipped_track(self, track: dict,
                                   spotify_client: SpotifyApiClient):
        """A callback that calls each addon on this playlist to handle the skipped track.

        Args:
            track: The track information of the skipped track.
            spotify_client: A client to make spotify requests with.
        """
        print("Handle skipped track")
        # await AutoAddPlaylist(self._playlist, self._user_id).handle_fully_listened_track(track, spotify_client)

    async def handle_fully_listened_track(self, track: dict,
                                          spotify_client: SpotifyApiClient):
        """A callback that calls each addon on this playlist to handle a fully listened track.

        Args:
            track: The track information of the skipped track.
            spotify_client: A client to make spotify requests with.
        """
        print("Handle fully listened track")
