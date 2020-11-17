"""Main module."""

import asyncio
import logging
from spotify_playlist_additions.playlists.abstract import AbstractPlaylist
from typing import List, Type
from async_spotify.authentification.authorization_flows.authorization_code_flow import AuthorizationCodeFlow

import requests

from async_spotify import SpotifyApiClient
from async_spotify.authentification import SpotifyAuthorisationToken
from async_spotify.authentification.authorization_flows import ClientCredentialsFlow

from aiohttp import web

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

        self._playlist = playlist or {}
        self._search_wait = search_wait

        
        uninit_addons = self._collect_addons()

        self._scope = self._get_scope(uninit_addons)
        
        self._spotify_client = SpotifyApiClient(AuthorizationCodeFlow(application_id="09259c4cc7854ead9bfd6fdac3ad9a0a",
                                                                      application_secret="fcf8cfb0ad5946408f1138af4cc48139",
                                                                      scopes=self._scope,
                                                                      redirect_url="http://localhost:8888/callback"),
                                                hold_authentication=True)
        
        self._user_id: str = ""
        
    async def connect_user(self):
        auth_url = self._spotify_client.build_authorization_url(show_dialog=True)
        # TODO: Will need to be replaced
        self._spotify_client.open_oauth_dialog_in_browser()
        
        
        await self._spotify_client.get_auth_token_with_code()
        await self._spotify_client.create_new_client()
        self._user_id = (await self._spotify_client.user.me())["id"]

    async def start(self) -> None:
        """Main loop for the program
        """

        prev_track = None
        remaining_duration = self._search_wait + 1
        while True:
            track = None
            try:
                track = await self._spotify_client.player.get_current_track()
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
                    tasks.append(addon.handle_skipped_track(prev_track, self._spotify_client))

            elif _detect_fully_listened_track(remaining_duration,
                                              self._search_wait):
                LOG.info("Detected fully listened song: %s",
                         prev_track["item"]["name"])
                for addon in self._playlist_addons:
                    tasks.append(addon.handle_fully_listened_track(prev_track, self._spotify_client))

            progress_ms = track["progress_ms"]
            duration_ms = track["item"]["duration_ms"]
            remaining_duration = duration_ms - progress_ms
            prev_track = track

            await asyncio.gather(*tasks)

            LOG.debug("Waiting %s seconds before testing tracks again",
                      self._search_wait / 1000)
            await asyncio.sleep(self._search_wait / 1000)

    async def choose_playlist_cli(self) -> None:
        """Simple interface to choose the playlist. Will be improved upon later on.
        """

        print("Select the playlist you want to use")

        playlists = await self._spotify_client.playlists.get_user_all(self._user_id)
        for idx, playlist in enumerate(playlists["items"]):
            print(str(idx) + ":", playlist["name"])

        # TODO: Make this not shit
        while True:
            user_input = input("Select a number: ")

            try:
                self._playlist = playlists["items"][int(user_input)]
                break
            except ValueError:
                pass

    def _collect_addons(self) -> List[AbstractPlaylist]:
        """Collects the addons specified in the config file
        """

        addons = []
        addons.append(AutoAddPlaylist)
        addons.append(AutoRemovePlaylist)
        
        return addons
        
    def _init_addons(self):
        for index in range(len(self._playlist_addons)):
            self._playlist_addons[index] = self._playlist_addons[index](
                self._spotify_client, self._playlist, self._user_id)

    def _get_scope(self, addons: List[AbstractPlaylist]) -> List[str]:
        """Collects the scope of all the addons into a singular scope, used to make a singular scope request to
        spotify
        """

        scope = []
        for addon in addons:
            scope.append(addon.scope)
            
        return scope
