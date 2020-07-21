"""Console script for spotify_playlist_additions."""
import argparse
import sys
import logging
import asyncio

from spotify_playlist_additions.spotify_playlist_additions import FluidPlaylist

log_format = '%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
logging.basicConfig(format=log_format,
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)
LOG = logging.getLogger(__name__)


def main():
    """Console script for spotify_playlist_additions."""
    parser = argparse.ArgumentParser()
    parser.add_argument('_', nargs='*')
    args = parser.parse_args()

    LOG.info("Arguments: " + str(args._))

    playlist = FluidPlaylist()
    playlist.choose_playlist_cli()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(playlist.start())
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
