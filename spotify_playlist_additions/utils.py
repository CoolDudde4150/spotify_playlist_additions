from spotify_playlist_additions.playlists.abstract import AbstractPlaylist
from typing import Any, Awaitable, List, Optional, TypeVar, Tuple

import asyncio
import functools
import traceback

T = TypeVar('T')


def create_task(
    coroutine: Awaitable[T],
    *,
    loop: Optional[asyncio.AbstractEventLoop] = None,
):
    """
    Believe it or not, asyncio does not actually raise an error if a task with a name assigned to
    it raises an error

    This helper function wraps a ``loop.create_task(coroutine())`` call and ensures there is
    an exception handler added to the resulting task. If the task raises an exception it is logged
    using the provided ``logger``, with additional context provided by ``message`` and optionally
    ``message_args``.
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    task = loop.create_task(coroutine)
    task.add_done_callback(functools.partial(handle_task_result))
    return task


def handle_task_result(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # Task cancellation should not be logged as an error.
    # Ad the pylint ignore: we want to handle all exceptions here so that the result of the task
    # is properly logged. There is no point re-raising the exception in this callback.
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()


def detect_skipped_track(remaining_duration: float, end_of_track_buffer: float,
                         track: dict, prev_track: dict) -> bool:
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


def detect_fully_listened_track(remaining_duration,
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


def get_scope(addons: List[AbstractPlaylist]) -> List[str]:
    """Collects the scope of all the addons into a singular scope, used to make a singular scope request to
    spotify
    """

    scope = []
    for addon in addons:
        scope.append(addon.scope)

    return scope
