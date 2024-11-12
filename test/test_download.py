import unittest
# from pathlib import Path

from src.net_dl import download


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

    # def test_check_integrity(self):
    #     remote_svg = 'https://httpbin.org/image/svg'
    #     destdir = Path(__file__).parent
    #     local_svg = destdir / 'svg'
    #     download.Download(remote_svg)

    def test_is_file(self):
        urls = {
            'https://httpbin.org/html': False,
            'https://httpbin.org/image/svg': True,
            'https://httpbin.org/json': False,
            'https://httpbin.org/robots.txt': False,
            'https://httpbin.org/xml': False,
        }
        for url, result in urls.items():
            dl = download.Download(url)
            dl.url.get_head_response()
            self.assertIs(
                dl.url.is_file,
                result,
                f"{url}: {result}; {dl.url.is_file}"
            )
