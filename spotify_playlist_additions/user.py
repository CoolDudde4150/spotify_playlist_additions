"""Contains logic for a singular user connecting to a Spotify Playlist Additions instance.

Users maintain separation by running an instance of the main loop checks on that users tracks
"""

import asyncio
import logging
from asyncio import Task

from spotify_playlist_additions.utils import detect_fully_listened_track, detect_skipped_track, create_task
from requests.exceptions import ReadTimeout
from spotify_playlist_additions.playlist import SpotifyPlaylist
from typing import List
from async_spotify.api.spotify_api_client import SpotifyApiClient

LOG = logging.getLogger(__name__)


class SpotifyUser:
    """A user class that will be created each time someone connects through the web application.

    Each user should represent a different Spotify account, where a User has multiple managed playlists
    """

    def __init__(self, client: SpotifyApiClient, search_wait: int):
        """Initializes a user with its own SpotifyApiClient to make requests with.

        Starting this class requires an internet connection

        Args:
            client: An ApiClient that can be used to make requests on behalf of the user. Will
                only contain the required scopes as indicated by the selected playlist types
            search_wait: How many milliseconds between running each playlist addon
        """
        self._client = client
        self._user_id = ""
        self._playlist = dict()
        self._playlists: List[SpotifyPlaylist] = list()
        self._search_wait = search_wait
        self._continue = True
        self._tasks: List[Task] = []

    async def start(self):
        """
        Does any asynchronous startup functions and starts any background tasks required for
        function. Notably, starts the infinite loop of checking every search_wait amount of time.
        Not a blocking call, starts it in the background.
        """
        self._user_id = (await self._client.user.me())["id"]
        await self.choose_playlist_cli()

        LOG.info("Starting user %s", (await
                                      self._client.user.me())["display_name"])

        self._continue = True
        self._tasks.append(create_task(self.main_loop()))

    async def stop(self):
        """
        Stops any asynchronous tasks that were started with the start function
        """
        self._continue = False
        await asyncio.gather(*self._tasks)

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
        """
        The main loop of a user, that runs every playlist upon certain events occurring.
        """
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
