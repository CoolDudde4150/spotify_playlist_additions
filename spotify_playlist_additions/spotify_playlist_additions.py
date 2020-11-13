"""Main module."""

import asyncio
import logging

import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from spotify_playlist_additions.playlists.autoadd import AutoAddPlaylist
from spotify_playlist_additions.playlists.autoremove import AutoRemovePlaylist

LOG = logging.getLogger(__name__)


def _detect_skipped_track(remaining_duration: float,
                          end_of_track_buffer: float, track: dict,
                          prev_track: dict) -> bool:
    """Performs the detection logic for whether a track was skipped

    Args:
        remaining_duration: The remaining duration of the track in milliseconds
        end_of_track_buffer: The buffer of time at the end of a song that, if skipped, will still be counted as fully
            listened
        track: The track retrieved directly from the spotify API.
        prev_track: The track that was detected to be playing on the previous frame.

    Returns:
        bool: Whether the track has been skipped or not.
    """

    if remaining_duration > end_of_track_buffer and prev_track["item"][
            "name"] != track["item"]["name"]:
        return True

    return False


def _detect_fully_listened_track(remaining_duration,
                                 end_of_track_buffer) -> bool:
    """Performs the detection logic for whether a track was fully listened through

    Args:
        remaining_duration: The remaining duration of the track in milliseconds
        end_of_track_buffer: The amount of milliseconds at the end of the song that will still count as fully listened.

    Returns:
        bool: Whether the track has been fully listened through or not.
    """

    if remaining_duration < end_of_track_buffer:
        return True
    return False


class SpotifyPlaylistEngine:
    """The main driver for Spotify Playlist Additions. Contains the main loop, functionality branches out from here.
    Contains logic for detection of a skipped or fully listened track and passes this information to various playlist
    additions that utilize it to perform actions on a playlist
    """
    def __init__(self, search_wait: float = 5000, playlist: dict = None):
        """Initializer for a SpotifyPlaylistEngine. Nothing that absolutely requires an internet connection should be
        located here.

        Args:
            search_wait: How long to wait before performing a track search. Essentially, the rate of checking or time
            per frame
            playlist: The playlist dictionary retrieved directly from the spotify API.
        """

        self._playlist = playlist
        self._search_wait = search_wait

        self._playlist_addons = []
        self._collect_addons()

        self._scope = ""
        self._get_scope()

        self._spotify_client = Spotify(auth_manager=SpotifyOAuth(
            redirect_uri="http://localhost:8888/callback",
            scope=self._scope,
            cache_path=".tokens.txt"))

        self._user_id: str = ""

    async def start(self) -> None:
        """Main loop for the program
        """

        self._user_id = self._spotify_client.current_user()["id"]
        self._init_addons()

        prev_track = None
        remaining_duration = self._search_wait + 1
        while True:
            track = None
            try:
                track = self._spotify_client.currently_playing()
            except requests.exceptions.ReadTimeout as exc:
                LOG.debug(exc)
                LOG.warning(
                    "Retrieving currently running track from spotify timed out.",
                    " See debug for more detail (this is unlikely to be a problem)"
                )
            except Exception as e:
                LOG.error(e)
            if not track:
                continue

            if not prev_track:
                prev_track = track

            if track["item"]["id"] != prev_track["item"]["id"]:
                LOG.info("Detected song start: %s", track["item"]["name"])

            tasks = []

            if _detect_skipped_track(remaining_duration, self._search_wait,
                                     track, prev_track):

                LOG.info("Detected skipped song: %s",
                         prev_track["item"]["name"])
                for addon in self._playlist_addons:
                    tasks.append(addon.handle_skipped_track(track=prev_track))

            elif _detect_fully_listened_track(remaining_duration,
                                              self._search_wait):
                LOG.info("Detected fully listened song: %s",
                         prev_track["item"]["name"])
                for addon in self._playlist_addons:
                    tasks.append(addon.handle_fully_listened_track(prev_track))

            progress_ms = track["progress_ms"]
            duration_ms = track["item"]["duration_ms"]
            remaining_duration = duration_ms - progress_ms
            prev_track = track

            await asyncio.gather(*tasks)

            LOG.debug("Waiting %s seconds before testing tracks again",
                      self._search_wait / 1000)
            await asyncio.sleep(self._search_wait / 1000)

    def choose_playlist_cli(self) -> None:
        """Simple interface to choose the playlist. Will be improved upon later on.
        """

        print("Select the playlist you want to use")

        playlists = self._spotify_client.current_user_playlists()
        for idx, playlist in enumerate(playlists["items"]):
            print(str(idx) + ":", playlist["name"])

        # TODO: Make this not shit
        while True:
            user_input = input("Select a number: ")

            try:
                self._playlist = playlists["items"][int(user_input)]
                break
            except:  # noqa: E722
                pass

    def _collect_addons(self):
        """Collects the addons specified in the config file
        """

        self._playlist_addons.append(AutoAddPlaylist)
        self._playlist_addons.append(AutoRemovePlaylist)

    def _init_addons(self):
        """Initializes addons with the required inputs
        """

        for index in range(len(self._playlist_addons)):
            self._playlist_addons[index] = self._playlist_addons[index](
                self._spotify_client, self._playlist, self._user_id)

    def _get_scope(self):
        """Collects the scope of all the addons into a singular scope, used to make a singular scope request to
        spotify
        """

        for addon in self._playlist_addons:
            self._scope += addon.scope + " "
