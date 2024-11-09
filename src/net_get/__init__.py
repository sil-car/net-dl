import argparse
import logging
from os import getcwd

from . import config
from .download import get

__version__ = '0.1'


def main():
    parser = argparse.ArgumentParser(prog="net-get")
    parser.add_argument(
        'url', metavar='URL', nargs='*',
        help="source URL(s) to download from",
    )
    parser.add_argument(
        '-c', '--continue-download', action='store_true',
        help="attempt to resume a partially-downloaded file"
    )
    parser.add_argument(
        '-d', '--output-directory', nargs=1,
        help="destination folder for downloaded file(s)",
    )
    parser.add_argument(
        '-H', '--header', action='append', default=dict(),
        help="add header to the server request (can be repeated): \"X-First-Name: Joe\""  # noqa: E501
    )
    parser.add_argument(
        '-n', '--filename', nargs=1,
        help="downloaded file's name (overrides name given by server)",
    )
    parser.add_argument(
        '-t', '--timeout', nargs=1, type=int,
        help=f"set server timeout in seconds [default={config.HTTP_TIMEOUT}]",
    )
    parser.add_argument(
        '--debug', action='store_true', help=argparse.SUPPRESS,
    )

    args = parser.parse_args()
    destdir = getcwd()
    resume = False

    # Set up logging.
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(
        level=log_level,
        format=config.MSG_FMT,
        datefmt=config.DATE_FMT,
    )
    logging.debug(f"{args=}")

    if args.continue_download:
        resume = True
    if args.timeout:
        config.HTTP_TIMEOUT = args.timeout[0]
    if args.output_directory:
        destdir = args.output_directory[0]
    destname = None
    if args.filename:
        destname = args.filename
    headers = {}
    for hstr in args.header:
        k, v = hstr.split(':')
        headers[k.strip()] = v.strip()
    for url in args.url:
        get(
            url,
            destdir=destdir,
            destname=destname,
            headers=headers,
            resume=resume,
        )