import argparse
import logging
from pathlib import Path
from os import getcwd
from sys import exit as sys_exit
from sys import stderr

from . import config
from .download import Download

__version__ = '0.2.0'


def main():
    parser = argparse.ArgumentParser(prog="net-dl")
    parser.add_argument(
        'url', metavar='URL', type=str, nargs='?',
        help="source URL(s) to download from",
    )
    parser.add_argument(
        '-c', '--continue-download', action='store_true',
        help="attempt to resume a partially-downloaded file"
    )
    parser.add_argument(
        '-d', '--output-directory', type=Path,
        help="destination folder for downloaded file(s)",
    )
    parser.add_argument(
        '-H', '--header', action='append', default=dict(),
        help="add header to the server request (can be repeated): \"X-First-Name: Joe\""  # noqa: E501
    )
    parser.add_argument(
        '-n', '--filename', type=str,
        help="downloaded file's name (overrides name given by server)",
    )
    parser.add_argument(
        '-t', '--timeout', type=int,
        help=f"set server timeout in seconds [default={config.HTTP_TIMEOUT}]",
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help="verbose output",
    )
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--debug', action='store_true', help=argparse.SUPPRESS,
    )

    args = parser.parse_args()
    destdir = getcwd()
    resume = False

    # Set up logging.
    log_level = logging.WARNING
    if args.verbose:
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
        config.HTTP_TIMEOUT = args.timeout
    if args.output_directory:
        destdir = args.output_directory
    destname = None
    if args.filename:
        destname = args.filename
    headers = {}
    for hstr in args.header:
        k, v = hstr.split(':')
        headers[k.strip()] = v.strip()
    try:
        return Download(
            url=args.url,
            destdir=destdir,
            destname=destname,
            request_headers=headers,
            resume=resume,
        ).get()
    except KeyboardInterrupt:
        print("Cancelled with Ctrl+C", file=stderr)
        sys_exit(1)
