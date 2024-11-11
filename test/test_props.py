import requests
import unittest
from pathlib import Path

import src.net_dl


class TestProps(unittest.TestCase):
    def setUp(self):
        self.p = src.net_dl.props.Props(__file__)

    def test_uri(self):
        print(self.p.path)
        assert self.p.path == __file__


class TestLocalFile(unittest.TestCase):
    def setUp(self):
        self.f = Path('./test.txt')
        self.f_text = "test file text\n"
        self.f.write_text(self.f_text)
        self.p = src.net_dl.props.LocalFile(str(self.f))

    def test_path(self):
        self.assertTrue(isinstance(self.p.path, Path))
        self.assertGreater(len(f"{self.p.path}"), 0)
        self.assertEqual(f"{self.p.path}", f"{self.f}")

    def test_size(self):
        self.assertIsNotNone(self.p.size)
        self.assertEqual(self.p.size, len(self.f_text))

    def test_mtime(self):
        old = self.p.get_mtime()
        self.assertIsNotNone(old)
        self.p.set_mtime('Wed, 21 Oct 2015 07:28:00 GMT')
        self.assertNotEqual(old, self.p.get_mtime())

    def tearDown(self):
        self.f.unlink()


class TestUrl(unittest.TestCase):
    def setUp(self):
        self.url = 'https://ip.me'
        self.p = src.net_dl.props.Url(self.url)
        # NOTE: This will make a connection to the URL and be a bit slow.
        self.p.get_head_response()

    def test_init(self):
        self.assertTrue(
            isinstance(
                self.p.head_response.headers,
                requests.structures.CaseInsensitiveDict
            )
        )
        self.assertEqual(
            self.p.head_response.headers.get('Content-Type'),
            'text/plain; charset=utf-8'
        )
        # TODO: Pick a different link to test MD5?
