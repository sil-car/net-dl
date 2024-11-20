import logging
import requests
import shutil
import sys
import threading
from os import getcwd
from pathlib import Path
from queue import Empty
from queue import Queue
from time import sleep
from urllib.parse import unquote

from . import config
from .props import LocalFile
from .props import Url


class Download:
    def __init__(
        self,
        url=None,
        destdir=getcwd(),
        destname=None,
        request_headers=None,
        chunk_size=None,
        progress_queue=None,
        remove_on_error=True,
        resume=None,
        timeout=config.HTTP_TIMEOUT,
        callback=None,
        callback_args=list(),
        callback_kwargs=dict(),
    ):
        self.url = Url(url)
        self.is_file = None
        self.destdir = Path(destdir)
        self.request_headers = dict()
        if request_headers:
            self.request_headers = request_headers
        if not self.request_headers.get('Accept-Encoding'):
            self.request_headers['Accept-Encoding'] = 'identity'
        self.chunk_size = chunk_size
        self.progress_queue = progress_queue
        self.remove_on_error = remove_on_error
        self.resume = resume
        self.timeout = timeout
        self.callback = callback
        self.callback_args = callback_args
        self.callback_kwargs = callback_kwargs

    def get(self):
        self.url._ensure_head_response()
        if self.url.head_response is None:
            logging.error(f"No header response from \"{self.url}\"")
            return 1
        if self.url.head_response.status_code != 200:
            if self.url.head_response.status_code == 404:
                logging.error(
                    f"{self.url.head_response.status_code}: "
                    f"{self.url.head_response.reason}"
                )
                return 1
            else:
                logging.debug(self.url.head_response.__dict__)
                logging.error(
                    f"{self.url.head_response.status_code}: "
                    f"{self.url.head_response.reason}"
                )
                return 1
        if self.chunk_size is None:
            # Ensure at least 2 chunks so that progress queue doesn't hang.
            self.chunk_size = min(round(self.url.size / 2), 100*1024)
        if self.url.is_file:
            self.get_file()
        else:
            self.get_text()
        return 0

    def get_content(self):
        return self._get_completed_request_obj()._content

    def get_text(self):
        ''' Content-Type is "text", etc., return decoded text. '''
        r = self._get_completed_request_obj()
        if r:
            print(r.text)

    def get_file(self, file_mode='wb'):
        ''' Content-Type is "application", show progress and save to file. '''

        # Determine progress queue.
        if self.progress_queue is None:
            use_own_queue = True
            self.progress_queue = Queue()
        else:
            use_own_queue = False

        # Determine output filename.
        # TODO: Make filename an attribute of the Url object.
        filename = self.url._get_content_disposition_filename()
        if filename is None:  # get from URL
            filename = unquote(self.url.final_url.split('/')[-1])
        self.dest = LocalFile(self.destdir / filename)
        logging.debug(f"{str(self.dest)=}")

        # If file exists try to resume download.
        self.remaining_size = self.url.size
        if self.dest.path.is_file():
            logging.debug(f"Destination file exists: {self.dest.path}")
            local_size = self.dest.get_size()
            logging.debug(f"Current downloaded size [B]: {local_size}")
            if (
                self.resume
                and local_size < self.url.size
                and self.url.head_response.headers.get('Accept-Ranges') == 'bytes'  # noqa: E501
                and self._check_server_accepts_range()
            ):
                logging.debug("Resuming download.")
                file_mode = 'ab'
                if isinstance(self.url.size, int):
                    self.remaining_size = self.url.size - local_size
                    self.request_headers['Range'] = f'bytes={local_size}-{self.url.size}'  # noqa: E501
                else:
                    self.requeset_headers['Range'] = f'bytes={local_size}-'
            elif local_size == self.url.size:
                logging.debug("File already downloaded. Verifying integrity.")
                sum_type = None
                if self.url.md5:
                    sum_type = 'md5'
                if self._check_integrity(sum_type=sum_type):
                    logging.info(f"File already exists: {self.dest.path}")
                    return
                else:
                    logging.debug("Redownloading file.")
            else:
                logging.debug("Local file size mismatch; restarting download.")

        # Log download type.
        if 'Range' in self.request_headers.keys():
            verb = "Continuing"
        else:
            verb = "Starting new"
        logging.info(f"{verb} download from: {self.url.path}")

        # Check for available disk space.
        if not self._check_disk_space():
            logging.critical("Not enough disk space.")
            # sys.exit(1)
            return

        # Start download thread.
        t = threading.Thread(
            target=self._get_stream_request,
            kwargs={'file_mode': file_mode},
            daemon=True,
        )
        logging.debug("Starting stream request download thread.")
        t.start()
        # Show download progress.
        while t.is_alive():
            if use_own_queue:
                try:
                    p = self.progress_queue.get(timeout=10)
                except Empty:
                    continue  # checks to see if thread is still alive
                self._write_progress_bar(p)
            else:
                sleep(0.1)
        if use_own_queue and sys.stdout.isatty():
            print()  # newline after progress bar is done

        logging.info(f"File saved as: {self.dest.path}")
        if not self._check_integrity():
            logging.critical("Integrity check failed")
            sys.exit(1)

    def _check_server_accepts_range(self):
        # Ref: https://stackoverflow.com/a/50635525
        accepts = False
        request_headers = {'Range': 'bytes=0-1'}
        url = Url(self.url.path, request_headers=request_headers)
        r = url.get_head_response()
        logging.debug(f"Accepts Range check: {r.status_code=}; {r.headers=}")
        if r.status_code == 206 and 'Content-Range' in r.headers.keys():
            accepts = True
        return accepts

    def _check_disk_space(self):
        free = shutil.disk_usage(self.dest.path.parent).free
        logging.info(f"{self.remaining_size} B needed; {free} B available")
        if self.remaining_size > free:
            return False
        return True

    def _check_integrity(self, sum_type=None):
        result = True
        if not self.dest.path.is_file():
            logging.error(f"File does not exist: {self.dest.path}")
            result = False
        if result and self.url.size:
            result = self.dest.size == self.url.size
            logging.info(f"Size on server: {self.url.size}; downloaded size: {self.dest.size}")  # noqa: E501
            logging.debug(f"Same size: {result}")
        if result and sum_type == 'md5':
            logging.info(f"MD5 on server: {self.url.md5}; downloaded MD5: {self.dest.md5}")  # noqa: E501
            result = self.dest.md5 == self.url.md5
            logging.debug(f"Same MD5: {result}")
        return result

    def _get_completed_request_obj(self):
        try:
            r = requests.get(
                str(self.url),
                headers=self.request_headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
        except config.HTTP_ERRORS as e:
            if isinstance(e, requests.exceptions.ConnectionError):
                logging.error(e)
            else:
                logging.error(f"{type(e)}: {e}")
                return
        return r

    def _get_stream_request(self, file_mode='wb'):
        logging.debug(f"Download._get_stream_request for: {self.url}")
        logging.debug(f"{self.request_headers=}")
        logging.debug(f"{self.chunk_size=}")
        logging.debug(f"{self.timeout=}")
        try:
            with requests.get(
                str(self.url),
                stream=True,
                headers=self.request_headers,
                timeout=self.timeout,
                allow_redirects=True,
            ) as r:
                logging.debug(f"Response {r.headers=}")
                with self.dest.path.open(mode=file_mode) as f:
                    if file_mode == 'wb':
                        verb = 'Writing'
                    elif file_mode == 'ab':
                        verb = 'Appending'
                    logging.debug(f"{verb} data to file: {self.dest.path}")
                    for chunk in r.iter_content(chunk_size=self.chunk_size):
                        f.write(chunk)
                        # Send progress value to queue param.
                        local_size = self.dest.get_size()
                        percent = round(local_size / self.url.size * 100)
                        self.progress_queue.put(percent)
                        if self.callback:
                            self.callback(
                                *self.callback_args,
                                **self.callback_kwargs,
                            )
        except config.HTTP_ERRORS as e:
            if sys.stdout.isatty():
                print()
            if isinstance(e, requests.exceptions.ConnectionError):
                logging.error(e)
            else:
                logging.error(f"{type(e)}: {e}")
            if self.remove_on_error:
                logging.info(f"Deleting file: {self.dest.path}")
                self.dest.path.unlink()
            return

        # Set file's mtime from server.
        url_mtime = r.headers.get('Last-Modified')
        if url_mtime:
            self.dest.set_mtime(url_mtime)

    def _write_progress_bar(self, percent):
        screen_width = shutil.get_terminal_size((80, 24)).columns
        y = '.'
        n = ' '
        l_f = int(screen_width * 0.75)  # progress bar length
        l_y = int(l_f * percent / 100)  # num. of chars. complete
        l_n = l_f - l_y  # num. of chars. incomplete
        # end='\x1b[1K\r' to erase to end of line
        if sys.stdout.isatty():
            print(f" [{y * l_y}{n * l_n}] {percent:>3}%", end='\r')
