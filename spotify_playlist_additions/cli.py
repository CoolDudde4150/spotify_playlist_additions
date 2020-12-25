"""Console script for spotify_playlist_additions."""
import argparse
import sys
import logging
import asyncio

from spotify_playlist_additions.spotify_playlist_additions import SpotifyPlaylistEngine

log_format = '%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
logging.basicConfig(format=log_format,
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)
LOG = logging.getLogger(__name__)


async def main():
    """Console script for spotify_playlist_additions."""
    parser = argparse.ArgumentParser()
    parser.add_argument('_', nargs='*')
    args = parser.parse_args()

    LOG.info("Arguments: " + str(args._))
    engine = SpotifyPlaylistEngine(search_wait=200)
    await engine.start()
    await asyncio.sleep(1000000)
    return 0


def start():
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(main())


if __name__ == "__main__":
    sys.exit(start())  # pragma: no cover
