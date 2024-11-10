import unittest

from src.net_get import download


class TestDownload(unittest.TestCase):
    def test_dns_error(self):
        url = 'https://does.not/exist'
        d = download.Download(url)
        self.assertIsNone(d.url.get_head_response())
        self.assertEqual(d.get(), 1)

    def test_404(self):
        url = 'https://httpbin.org/status/404'
        self.assertEqual(download.Download(url).get(), 1)

    def test_30X(self):
        statuses = [301, 302]
        url2 = 'https://httpbin.org'
        url2_esc = 'https%3A%2F%2Fhttpbin.org'
        for s in statuses:
            url1 = f'https://httpbin.org/redirect-to?url={url2_esc}&status={s}'
            d = download.Download(url1)
            self.assertEqual(d.get(), 0)
            self.assertEqual(d.url.final_url, url2)
