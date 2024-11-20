import unittest
from pathlib import Path

from src.net_dl import download


class TestDownload(unittest.TestCase):
    def test_30X(self):
        statuses = [301, 302]
        url2 = 'https://httpbin.org'
        url2_esc = 'https%3A%2F%2Fhttpbin.org'
        for s in statuses:
            url1 = f'https://httpbin.org/redirect-to?url={url2_esc}&status={s}'
            d = download.Download(url1)
            self.assertEqual(d.get(), 0)
            self.assertEqual(d.url.final_url, url2)

    def test_404(self):
        url = 'https://httpbin.org/status/404'
        self.assertEqual(download.Download(url).get(), 1)

    def test_dns_error(self):
        url = 'https://does.not/exist'
        d = download.Download(url)
        self.assertIsNone(d.url._get_head_response())
        self.assertEqual(d.get(), 1)

    def test_file_download(self):
        url = 'https://httpbin.org/image/svg'
        dest = Path(url.split('/')[-1])
        d = download.Download(url)
        d.get()
        self.assertEqual(d.url.size, dest.stat().st_size)
        if dest.is_file():
            dest.unlink()
