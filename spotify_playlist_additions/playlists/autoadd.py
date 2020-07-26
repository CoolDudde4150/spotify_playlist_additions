import logging
from typing import Any

from spotify_playlist_additions.playlists.abstract import AbstractPlaylist

LOG = logging.getLogger(__name__)


class AutoAddPlaylist(AbstractPlaylist):
    async def start(self) -> Any:
        pass

    async def stop(self) -> Any:
        pass

    scope = "user-read-currently-playing playlist-modify-public"

    def handle_skipped_track(self, track: dict):
        pass

    async def handle_fully_listened_track(self, track: dict):
        if not self._playlist_contains_track(track):
            LOG.info("Added %s to playlist", track["item"]["name"])
            self._spotify_client.user_playlist_add_tracks(
                self._user_id, self._playlist["id"], [track["item"]["id"]])

    def _playlist_contains_track(self, track: dict) -> bool:
        LOG.info("Performing a search for %s", track["item"]["name"])

        length = 100
        offset = 0
        while length == 100:
            playlist_tracks = self._spotify_client.playlist_tracks(
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

        LOG.info("Finished searching playlist for %s", track["item"]["name"])

        return False
