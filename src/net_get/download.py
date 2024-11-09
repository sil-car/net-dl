import logging
import queue
import re
import requests
import shutil
import sys
import threading
import time
from os import getcwd
from pathlib import Path
from urllib.parse import unquote

from . import config
from .props import FileProps
from .props import UrlProps


def get(
    url,
    destdir=getcwd(),
    destname=None,
    headers=None,
    progress_queue=None,
    remove_on_error=True,
    resume=None,
    gui_callback=None,
    gui_callback_args=None,
    gui_callback_kwargs=None,
):
    logging.debug(f"Download source: {url=}")
    logging.debug(f"Download destination folder: {destdir=}")
    logging.debug(f"Download destination filename: {destname=}")

    deststr = None
    if destname:
        deststr = f"{destdir}/{destname}"
    dest = FileProps(deststr)  # sets path and size attribs

    url = UrlProps(url)  # uses requests to set headers, size, md5 attribs
    if url.headers is None:
        logging.warning("Could not get headers.")
        url.headers = {}
        return

    # Initialize variables.
    timeout = config.HTTP_TIMEOUT
    local_size = 0
    total_size = url.size  # None or int
    remaining_size = total_size  # for continued downloads
    logging.info(f"File size on server [B]: {total_size}")
    chunk_size = 512 * 1024  # 512 KB default; progress updates once per chunk
    chunk_size = 100 * 1024
    if not headers:
        headers = dict()
    if not headers.get('Accept-Encoding'):
        # Force non-compressed download.
        headers['Accept-Encoding'] = 'identity'
    file_mode = 'wb'

    # Determine output filename.
    tempname = None
    if not dest.path:
        logging.debug(f"{url.headers=}")
        # Try to determine filename from URL and headers.
        cd_name = None
        n = 5
        last_part = url.path.split('/')[-1]
        cd_str = url.headers.get('Content-Disposition')
        if cd_str:
            cd_name = get_content_disposition_filename(cd_str)
        if cd_name:  # get filename from Content-Disposition header
            dest.path = Path(f"{destdir}/{cd_name}")
        elif len(last_part) > n and '.' in last_part[-n:]:
            # Assume it's a filename; save to destdir
            dest.path = Path(f"{destdir}/{unquote(last_part)}")
        else:  # save to tempfile; move afterwards
            tempname = f".net_get-{time.strftime('%Y%m%dT%H%M%S')}"
            dest.path = Path(f"{destdir}/{tempname}")
    logging.debug(f"{dest.path=}")

    # If file exists try to resume download.
    if total_size and dest.path.is_file():
        logging.debug(f"Destination file exists: {dest.path}")
        local_size = dest.get_size()
        logging.debug(f"Current downloaded size [B]: {local_size}")
        if (
            resume
            and local_size < total_size
            and url.headers.get('Accept-Ranges') == 'bytes'
        ):
            logging.debug("Resuming download.")
            file_mode = 'ab'
            if isinstance(total_size, int):
                remaining_size = total_size - local_size
                headers['Range'] = f'bytes={local_size}-{total_size}'
            else:
                headers['Range'] = f'bytes={local_size}-'
        elif local_size == total_size:
            logging.debug("File already downloaded. Verifying integrity.")
            sum_type = None
            url_checksum = None
            if url.md5:
                sum_type = 'md5'
                url_checksum = url.md5
            if check_integrity(
                dest.path,
                sum_type=sum_type,
                url_checksum=url_checksum,
                url_size=url.size,
            ):
                logging.info(f"File already exists: {dest.path}")
                return
            else:
                logging.debug("Redownloading file.")
        else:
            logging.debug("Local file size mismatch; restarting download.")

    logging.debug(f"{chunk_size=}; {file_mode=}; {headers=}")

    # Log download type.
    if 'Range' in headers.keys():
        message = f"Continuing download from: {url.path}."
    else:
        message = f"Starting new download from: {url.path}."
    logging.info(message)

    # Check for available disk space.
    if total_size and not verify_disk_space(dest.path, remaining_size):
        logging.critical("Not enough disk space.")
        sys.exit(1)

    q = queue.Queue()
    if progress_queue:
        q = progress_queue

    t = threading.Thread(
        target=_download,
        args=[url.path],
        kwargs={
            'chunk_size': chunk_size,
            'destobj': dest,
            'file_mode': file_mode,
            'headers': headers,
            'progress_queue': q,
            'remove_on_error': remove_on_error,
            'tempname': tempname,
            'timeout': timeout,
            'total_size': total_size,
            'gui_callback': gui_callback,
            'gui_callback_args': gui_callback_args,
            'gui_callback_kwargs': gui_callback_kwargs,
        },
        daemon=True,
    )
    logging.debug("Starting download thread.")
    t.start()
    while t.is_alive():
        if not q.empty():
            _write_progress_bar(q.get())
        time.sleep(0.1)


def _download(
    url,
    chunk_size=None,
    destobj=None,
    file_mode='wb',
    headers=None,
    progress_queue=None,
    remove_on_error=True,
    tempname=None,
    timeout=config.HTTP_TIMEOUT,
    total_size=None,
    gui_callback=None,
    gui_callback_args=None,
    gui_callback_kwargs=None,
):
    try:
        with requests.get(
            url,
            stream=True,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        ) as r:
            with destobj.path.open(mode=file_mode) as f:
                if file_mode == 'wb':
                    mode_text = 'Writing'
                else:
                    mode_text = 'Appending'
                logging.debug(f"{mode_text} data to file: {destobj.path}")
                for chunk in r.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    if progress_queue and isinstance(total_size, int):
                        # Send progress value to queue param.
                        local_size = destobj.get_size()
                        percent = round(local_size / total_size * 100)
                        progress_queue.put(percent)
                        if gui_callback:
                            gui_callback(*gui_callback_args, **gui_callback_kwargs)  # noqa: E501
    except config.HTTP_ERRORS as e:
        if sys.stdout.isatty():
            print()
        if isinstance(e, requests.exceptions.ConnectionError):
            logging.error(e)
        else:
            logging.error(f"{type(e)}: {e}")
        if remove_on_error:
            logging.info(f"Deleting file: {destobj.path}")
            destobj.path.unlink()
        return

    if progress_queue and sys.stdout.isatty():
        progress_queue.put(100.0)
        time.sleep(0.15)
        print()  # newline after progress bar is done

    # Rename if tempname was used.
    logging.debug(f"URL: {r.url}")
    if tempname:
        name = r.url.split('/')[-1]
        if not name:
            name = tempname.lstrip('.')
        destobj.path = destobj.path.rename(destobj.path.with_name(name))
    logging.info(f"File saved as: {destobj.path}")

    # Set file's mtime from server.
    url_mtime = r.headers.get('Last-Modified')
    if url_mtime:
        destobj.set_mtime(url_mtime)


def _write_progress_bar(percent):
    screen_width = shutil.get_terminal_size((80, 24)).columns
    y = '.'
    n = ' '
    l_f = int(screen_width * 0.75)  # progress bar length
    l_y = int(l_f * percent / 100)  # num. of chars. complete
    l_n = l_f - l_y  # num. of chars. incomplete
    # end='\x1b[1K\r' to erase to end of line
    if sys.stdout.isatty():
        print(f" [{y * l_y}{n * l_n}] {percent:>3}%", end='\r')


def get_content_disposition_filename(cd_header_str):
    """
    'Content-Disposition':
     'attachment;
      filename="=?UTF-8?Q?avast=5Ffree=5Fantivirus=5Foffline=5Fsetup.exe?=";
      filename*=UTF-8\'\'avast_free_antivirus_offline_setup.exe'
    """
    fname = re.findall(
        r"filename\*=([^;]+)",
        cd_header_str,
        flags=re.IGNORECASE
    )
    if not fname:
        fname = re.findall(
            r"filename=([^;]+)",
            cd_header_str,
            flags=re.IGNORECASE
        )
    if fname[0].lower().startswith("utf-8''"):
        fname = re.sub(r"utf-8''", '', fname[0], flags=re.IGNORECASE)
        fname = unquote(fname)
    else:
        fname = fname[0]

    # Remove space and double quotes.
    return fname.strip().strip('"')


def verify_disk_space(destpath, file_length):
    destpath = Path(destpath)
    okay = True
    free = shutil.disk_usage(destpath.parent).free
    if file_length > free:
        okay = False
    logging.info(f"{file_length} B needed; {free} B available")
    return okay


def check_integrity(
    filepath,
    sum_type=None,
    url_checksum=None,
    url_size=None,
):
    fileobj = FileProps(filepath)
    result = True
    if not fileobj.path.is_file():
        logging.error(f"File does not exist: {filepath}")
        result = False
    if result and url_size:
        url_size = int(url_size)
        result = fileobj.size == url_size
        logging.debug(f"Same size: {result}")
    if result and sum_type == 'md5':
        result = fileobj.md5 == url_checksum
        logging.debug(f"Same MD5: {result}")
    return result
