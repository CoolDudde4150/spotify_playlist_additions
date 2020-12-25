import asyncio
import logging
from spotify_playlist_additions.utils import detect_fully_listened_track, detect_skipped_track, create_task
from requests.exceptions import ReadTimeout
from spotify_playlist_additions.playlist import SpotifyPlaylist
from typing import List
from async_spotify.api.spotify_api_client import SpotifyApiClient

LOG = logging.getLogger(__name__)


class SpotifyUser:
    def __init__(self, client: SpotifyApiClient, search_wait: int):
        self._client = client
        self._user_id = ""
        self._playlist = dict()
        self._playlists: List[SpotifyPlaylist] = list()
        self._search_wait = search_wait
        self._continue = True

    async def start(self):
        self._user_id = (await self._client.user.me())["id"]
        await self.choose_playlist_cli()

        LOG.info("Starting user %s", (await
                                      self._client.user.me())["display_name"])

        self._continue = True
        self._loop_task = create_task(self.main_loop())

    async def stop(self):
        self._continue = False
        await self._loop_task

    async def choose_playlist_cli(self) -> None:
        """Simple interface to choose the playlist. Will be improved upon later on.
        """
        print("Select the playlist you want to use")

        playlists = await self._client.playlists.get_user_all(self._user_id)
        for idx, playlist in enumerate(playlists["items"]):
            print(str(idx) + ":", playlist["name"])

        # TODO: Make this not shit
        while self._continue:
            user_input = input("Select a number: ")

            try:
                self._playlist = playlists["items"][int(user_input)]
                self._playlists.append(SpotifyPlaylist())
                break
            except ValueError:
                pass

    async def main_loop(self):
        prev_track = None
        remaining_duration = self._search_wait + 1
        while self._continue:
            await asyncio.sleep(self._search_wait / 1000)
            track = None
            try:
                track = await self._client.player.get_current_track()
            except ReadTimeout as exc:
                LOG.debug(exc)
                LOG.warning(
                    "Retrieving currently running track from spotify timed out.",
                    " See debug for more detail (this is unlikely to be a problem)"
                )

            if not track:
                continue

            if not prev_track:
                prev_track = track

            if track["item"]["id"] != prev_track["item"]["id"]:
                LOG.info("Detected song start: %s", track["item"]["name"])

            tasks = []

            if detect_skipped_track(remaining_duration, self._search_wait,
                                    track, prev_track):

                LOG.info("Detected skipped song: %s",
                         prev_track["item"]["name"])
                for playlist in self._playlists:
                    tasks.append(
                        playlist.handle_skipped_track(prev_track,
                                                      self._client))

            elif detect_fully_listened_track(remaining_duration,
                                             self._search_wait):
                LOG.info("Detected fully listened song: %s",
                         prev_track["item"]["name"])
                for playlist in self._playlists:
                    tasks.append(
                        playlist.handle_fully_listened_track(
                            prev_track, self._client))

            progress_ms = track["progress_ms"]
            duration_ms = track["item"]["duration_ms"]
            remaining_duration = duration_ms - progress_ms
            prev_track = track

            await asyncio.gather(*tasks)

            LOG.debug("Waiting %s seconds before testing tracks again",
                      self._search_wait / 1000)
