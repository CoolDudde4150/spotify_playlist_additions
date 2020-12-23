from spotify_playlist_additions.playlists.autoadd import AutoAddPlaylist
from async_spotify.api.spotify_api_client import SpotifyApiClient


class SpotifyPlaylist:
    # def __init__(self, playlist: dict, user_id: str):
    #     self._playlist = playlist
    #     self._user_id = user_id
    
    async def handle_skipped_track(self, track: dict, spotify_client: SpotifyApiClient):
        print("Handle skipped track")
        # await AutoAddPlaylist(self._playlist, self._user_id).handle_fully_listened_track(track, spotify_client)
    
    async def handle_fully_listened_track(self, track: dict, spotify_client: SpotifyApiClient):
        print("Handle fully listened track")
    
