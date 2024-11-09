import hashlib
import logging
import requests
from base64 import b64encode
from datetime import datetime
from os import utime
from pathlib import Path

from . import config


class Props:
    def __init__(self, uri=None):
        self.size = None
        self.md5 = None
        self.path = None
        if uri is not None:
            self.path = uri


class LocalFile(Props):
    def __init__(self, f=None):
        super().__init__(f)
        if f:
            self.path = Path(self.path)
            if self.path.is_file():
                self.get_size()
                # self.get_md5()

    def __str__(self):
        return str(self.path)

    def get_size(self):
        if self.path is None:
            return
        self.size = self.path.stat().st_size
        return self.size

    def get_md5(self):
        if self.path is None:
            return
        md5 = hashlib.md5()
        with self.path.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
        self.md5 = b64encode(md5.digest()).decode('utf-8')
        logging.debug(f"{self.path} MD5: {self.md5}")
        return self.md5

    def get_mtime(self):
        if not self.path:
            return
        return self.path.stat().st_mtime

    def set_mtime(self, http_timestamp):
        if not self.path.is_file():
            logging.error(
                f"Could not set timestamp; non-existant file: {self.path}"
            )
            return
        fmtstr = '%a, %d %b %Y %H:%M:%S %Z'
        timestamp = datetime.strptime(http_timestamp, fmtstr).timestamp()
        utime(self.path, (timestamp, timestamp))


class Url(Props):
    def __init__(
        self,
        url=None,
        request_headers=None,
        timeout=config.HTTP_TIMEOUT
    ):
        super().__init__(url)
        self.request_headers = {}
        if request_headers:
            self.request_headers = request_headers
        self.timeout = timeout
        self.head_response = None
        self.final_url = None
        self.size = None
        self.md5 = None
        self.is_file = None

    def __str__(self):
        return self.path

    def get_head_response(self):
        logging.debug(f"Getting headers from {self.path}.")
        try:
            # Force non-compressed txfr
            self.request_headers['Accept-Encoding'] = 'identity'
            r = requests.head(
                self.path,
                allow_redirects=True,
                headers=self.request_headers,
                timeout=self.timeout,
            )
        except config.HTTP_ERRORS as e:
            if isinstance(e, requests.exceptions.ConnectionError):
                logging.error(e)
            else:
                logging.error(f"{type(e)}: {e}")
            return
        self._set_is_file(r.headers)
        self.head_response = r
        self.final_url = r.url
        self.size = self.get_size()
        self.md5 = self.get_md5()
        return self.head_response

    def get_size(self):
        if self.head_response is None:
            r = self.get_head_response()
            if r is None:
                return
        content_length = self.head_response.headers.get('Content-Length')
        content_encoding = self.head_response.headers.get('Content-Encoding')
        if content_encoding is not None:
            logging.critical(f"The server requires receiving the file compressed as '{content_encoding}'.")  # noqa: E501
        logging.debug(f"{content_length=}")
        if content_length:
            self.size = int(content_length)
        return self.size

    def get_md5(self):
        content_md5 = None
        if self.head_response is None:
            r = self.get_head_response()
            if r is None:
                return
        if self.head_response.headers.get('server') == 'AmazonS3':
            # Ref:
            # https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html  # noqa: E501
            # https://teppen.io/2018/06/23/aws_s3_etags/
            # i.e. hexmd5(md5(part1)+md5(part2))-{number of parts}
            # So it seems unrealistic to use the etag if it's for a multi-part
            # file. There's a way to generate a local equivalent etag, but that
            # also seems unrealistic:
            # https://teppen.io/2018/10/23/aws_s3_verify_etags/
            if '-' not in self.head_response.headers.get('etag'):
                content_md5 = self.head_response.headers.get('etag')
            if content_md5:
                # Convert from hex to base64
                content_md5_hex = content_md5.strip('"').strip("'")
                content_md5 = b64encode(bytes.fromhex(content_md5_hex)).decode()  # noqa: E501
        else:
            content_md5 = self.head_response.headers.get('Content-MD5')
        if content_md5 is not None:
            content_md5 = content_md5.strip('"').strip("'")
        logging.debug(f"{content_md5=}")
        if content_md5 is not None:
            self.md5 = content_md5
        return self.md5

    def _set_is_file(self, response_headers):
        ''' Defaults to None '''
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type  # noqa: E501
        content_type = response_headers.get('Content-Type')
        content_type_parts = [p.strip() for p in content_type.split(';')]
        mime_type = content_type_parts[0]
        mime_main = mime_type.split('/')[0]
        if mime_main == 'application':
            self.is_file = True
        elif mime_main == 'text':
            self.is_file = False
