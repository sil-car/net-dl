import requests
import unittest
from pathlib import Path

import src.net_get


class TestProps(unittest.TestCase):
    def setUp(self):
        self.p = src.net_get.props.Props(__file__)

    def test_uri(self):
        print(self.p.path)
        assert self.p.path == __file__


class TestFileProps(unittest.TestCase):
    def setUp(self):
        self.f = Path('./test.txt')
        self.f_text = "test file text\n"
        self.f.write_text(self.f_text)
        self.p = src.net_get.props.FileProps(str(self.f))

    def test_path(self):
        assert isinstance(self.p.path, Path)
        assert len(f"{self.p.path}") > 0
        assert f"{self.p.path}" == f"{self.f}"

    def test_size(self):
        assert self.p.size is not None
        assert self.p.size == len(self.f_text)

    def test_mtime(self):
        old = self.p.get_mtime()
        assert old
        self.p.set_mtime('Wed, 21 Oct 2015 07:28:00 GMT')
        assert old != self.p.get_mtime()

    def tearDown(self):
        self.f.unlink()


class TestUrlProps(unittest.TestCase):
    def setUp(self):
        self.url = 'https://ip.me'
        # NOTE: This will make a connection to the URL and be a bit slow.
        self.p = src.net_get.props.UrlProps(self.url)

    def test_init(self):
        assert isinstance(
            self.p.headers,
            requests.structures.CaseInsensitiveDict
        )
        assert self.p.headers.get('Content-Type') == 'text/plain; charset=utf-8'  # noqa: E501
        # TODO: Pick a different link to test MD5?
