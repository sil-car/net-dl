from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from socket import timeout


DATE_FMT = '%Y-%m-%d %H:%M:%S'
MSG_FMT = '%(asctime)s %(levelname)s: %(message)s'

HTTP_TIMEOUT = 30
HTTP_ERRORS = (
    Timeout,
    ConnectionError,
    timeout,
    Exception,
)
