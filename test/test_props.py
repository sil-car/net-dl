import requests
import unittest
from pathlib import Path

import src.net_dl


class TestProps(unittest.TestCase):
    def setUp(self):
        self.p = src.net_dl.props.Props(__file__)

    def test_uri(self):
        self.assertEqual(self.p.path, __file__)


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
    def test__ensure_head_response(self):
        url = 'https://ip.me'
        orl_obj = src.net_dl.props.Url(url)
        # NOTE: This will make a connection to the URL and be a bit slow.
        orl_obj._ensure_head_response()
        self.assertTrue(
            isinstance(
                orl_obj.head_response.headers,
                requests.structures.CaseInsensitiveDict
            )
        )
        self.assertEqual(
            orl_obj.head_response.headers.get('Content-Type'),
            'text/plain; charset=utf-8'
        )
        # TODO: Pick a different link to test MD5?

    def test__is_file(self):
        urls = {
            'https://httpbin.org/html': False,
            'https://httpbin.org/image/svg': True,
            'https://httpbin.org/json': False,
            'https://httpbin.org/robots.txt': False,
            'https://httpbin.org/xml': False,
        }
        for url, result in urls.items():
            url_obj = src.net_dl.props.Url(url)
            url_obj._set_is_file()
            self.assertIs(
                url_obj.is_file,
                result,
                f"{url}: {result}; {url_obj.is_file}"
            )


class TestContentDispositionName(unittest.TestCase):
    def test_dropbox(self):
        # TODO: Find a more permanent URL?
        url = 'https://www.dropbox.com/scl/fo/x88k1o9wkcjqwut4zxtrv/AJRI10SuMponk_W3FNzo6Hc?rlkey=vawj53no9kqomavll1vncan8v&e=1&st=wkgzl7sj&dl=1'  # noqa: E501
        dropbox_url = src.net_dl.props.Url(url)
        self.assertEqual(
            dropbox_url._get_content_disposition_filename(),
            'Banda-Bambari(Linda) Discrepancies & Corrections.zip'
        )

    def test_none(self):
        url = 'https://httpbin.org/html'
        none_url = src.net_dl.props.Url(url)
        self.assertIsNone(none_url._get_content_disposition_filename())
