import hashlib
import logging
import re
import requests
from base64 import b64encode
from datetime import datetime
from os import utime
from pathlib import Path
from urllib.parse import unquote

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
    HEADER_TYPES = (requests.structures.CaseInsensitiveDict, dict)

    def __init__(
        self,
        url=None,
        request_headers=None,
        timeout=config.HTTP_TIMEOUT
    ):
        super().__init__(url)
        self.request_headers = {}
        if type(request_headers) in Url.HEADER_TYPES:
            self.request_headers = request_headers
        self.timeout = timeout
        self.head_response = None
        self.final_url = None
        self.size = None
        self.md5 = None
        self.is_file = None

    def __str__(self):
        return self.path

    def get_content_disposition_filename(cd_header_str):
        """ cd_header_str comes from r.headers.get('Content-Disposition'); e.g.

        'Content-Disposition':
        'attachment;
        filename="=?UTF-8?Q?avast=5Ffree=5Fantivirus=5Foffline=5Fsetup.exe?=";
        filename*=UTF-8\'\'avast_free_antivirus_offline_setup.exe'
        """
        if cd_header_str is None:
            return None

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

    def get_head_response(url, request_headers=None, timeout=None):
        head_response = None
        if not type(request_headers) in Url.HEADER_TYPES:
            request_headers = dict()
        if timeout is None:
            timeout = 10
        logging.debug(f"Getting headers from {url}.")
        # NOTE: Adding 'identity' encoding to header so that content will be
        # uncompressed, which allows for correct progress measurement. However,
        # this may cause problems with some types of content.
        request_headers['Accept-Encoding'] = 'identity'
        try:
            # Force non-compressed txfr
            head_response = requests.head(
                url,
                allow_redirects=True,
                headers=request_headers,
                timeout=timeout,
            )
        except requests.exceptions.ConnectionError as e:
            if 'Failed to resolve' in str(e):
                logging.error(f"Failed to resolve address: {url}")
            else:
                logging.error(f"ConnectionError: {e}")
        except config.HTTP_ERRORS as e:
            logging.error(f"{type(e)}: {e}")
        except Exception as e:
            logging.error(f"{type(e)}: {e}")
        if head_response is not None:
            logging.debug(f"head_response headers:{head_response.headers}")
        return head_response

    def get_md5(response_headers):
        content_md5 = None
        if response_headers.get('server') == 'AmazonS3':
            # Ref:
            # https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html  # noqa: E501
            # https://teppen.io/2018/06/23/aws_s3_etags/
            # i.e. hexmd5(md5(part1)+md5(part2))-{number of parts}
            # So it seems unrealistic to use the etag if it's for a multi-part
            # file. There's a way to generate a local equivalent etag, but that
            # also seems unrealistic:
            # https://teppen.io/2018/10/23/aws_s3_verify_etags/
            if '-' not in response_headers.get('etag'):
                content_md5 = response_headers.get('etag')
            if content_md5:
                # Convert from hex to base64
                content_md5_hex = content_md5.strip('"').strip("'")
                content_md5 = b64encode(bytes.fromhex(content_md5_hex)).decode()  # noqa: E501
        else:
            content_md5 = response_headers.get('Content-MD5')
        if content_md5 is not None:
            content_md5 = content_md5.strip('"').strip("'")
        logging.debug(f"{content_md5=}")
        return content_md5

    def get_size(response_headers):
        size = None
        if not type(response_headers) in Url.HEADER_TYPES:
            return None
        content_length = response_headers.get('Content-Length')
        if content_length is None:
            return None
        content_encoding = response_headers.get('Content-Encoding')
        if content_encoding is not None:
            logging.critical(f"The server requires receiving the file compressed as '{content_encoding}'.")  # noqa: E501
        logging.debug(f"{content_length=}")
        if content_length:
            size = int(content_length)
        return size

    def _ensure_head_response(self):
        if self.head_response is None:
            self._get_head_response()

    def _get_content_disposition_filename(self):
        self._ensure_head_response()
        cd_header_str = self.head_response.headers.get('Content-Disposition')
        return Url.get_content_disposition_filename(cd_header_str)

    def _get_head_response(self):
        if self.path is None:
            logging.error("No URL given.")
            return None
        self.head_response = Url.get_head_response(
            self.path,
            request_headers=self.request_headers,
            timeout=self.timeout,
        )
        if self.head_response is not None:
            # Set attributes that depend on response headers.
            self._set_is_file()
            self.final_url = self.head_response.url
            self.size = self._get_size()
            self.md5 = self._get_md5()
        return self.head_response

    def _get_md5(self):
        self._ensure_head_response()
        self.md5 = Url.get_md5(self.head_response.headers)
        return self.md5

    def _get_mime_info(self, content_type_str=None):
        if content_type_str is None:
            self._ensure_head_response()
            content_type_str = self.head_response.headers.get('Content-Type')
        content_type_parts = [p.strip() for p in content_type_str.split(';')]
        return content_type_parts[0].split('/')

    def _get_size(self):
        self._ensure_head_response()
        self.size = Url.get_size(self.head_response.headers)
        return self.size

    def _set_is_file(self):
        ''' Determines whether the URL's content is a file or not.
        True: content is downloaded and saved as a local file
        False|None: content is printed to stdout
        '''
        # https://www.w3.org/Protocols/rfc1341/4_Content-Type.html
        self._ensure_head_response()

        cd_filename = self._get_content_disposition_filename()
        content_type = self.head_response.headers.get('Content-Type')
        logging.debug(f"{content_type=}")
        mime_info = self._get_mime_info()
        if len(mime_info) >= 2:
            mime_type, mime_subtype = mime_info[:2]
        if cd_filename is not None:
            self.is_file = True
        elif mime_type == 'text':
            self.is_file = False
        elif mime_type == 'application' and mime_subtype in ['json', 'xml']:
            self.is_file = False
        else:
            # NOTE: Some types will likely not be handled correctly with a
            # simple "is file or not" property, but hopefully this handles most
            # cases.
            self.is_file = True
