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
    if remaining_duration > end_of_track_buffer and prev_track["item"]["name"] != track["item"]["name"]:
        return True

    return False


def _detect_fully_listened_track(remaining_duration,
                                 end_of_track_buffer):
    if remaining_duration < end_of_track_buffer:
        return True
    return False


class SpotifyPlaylistEngine:

    def __init__(self,
                 search_wait: float = 5000,
                 playlist: dict = None):

        self._playlist = playlist
        self._search_wait = search_wait

        self._playlist_addons = []
        self._collect_addons()
        self._scope = ""
        self._get_scope()
        self._spotify_client = Spotify(auth_manager=SpotifyOAuth(redirect_uri="http://localhost:8888/callback",
                                                                 scope=self._scope,
                                                                 cache_path=".tokens.txt"))

        self._user_id: str = ""

    async def start(self):
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
                LOG.info("Detected song start: %s",
                         track["item"]["name"])

            if _detect_skipped_track(remaining_duration, self._search_wait,
                                     track, prev_track):

                LOG.info("Detected skipped song: %s",
                         prev_track["item"]["name"])
                for addon in self._playlist_addons:
                    await addon.handle_skipped_track(track=prev_track)

            elif _detect_fully_listened_track(remaining_duration,
                                              self._search_wait):
                LOG.info("Detected fully listened song: %s",
                         prev_track["item"]["name"])
                for addon in self._playlist_addons:
                    await addon.handle_fully_listened_track(prev_track)

            progress_ms = track["progress_ms"]
            duration_ms = track["item"]["duration_ms"]
            remaining_duration = duration_ms - progress_ms
            prev_track = track

            LOG.debug("Waiting %s seconds before testing tracks again",
                      self._search_wait / 1000)
            await asyncio.sleep(self._search_wait / 1000)

    def choose_playlist_cli(self):

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
        self._playlist_addons.append(AutoAddPlaylist)
        self._playlist_addons.append(AutoRemovePlaylist)

    def _init_addons(self):
        for index in range(len(self._playlist_addons)):
            self._playlist_addons[index] = self._playlist_addons[index](self._spotify_client, self._playlist,
                                                                        self._user_id)

    def _get_scope(self):
        for addon in self._playlist_addons:
            self._scope += addon.scope + " "
