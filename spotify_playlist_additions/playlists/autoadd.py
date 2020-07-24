from spotipy import Spotify
from spotify_playlist_additions.playlists.abstract import AbstractPlaylist

class AutoAddPlaylist(AbstractPlaylist):
    scope = "user-read-currently-playing playlist-modify-public"

    def handle_skipped_track(self, track):
        pass

    def handle_fully_listened_track(self, track):
        pass