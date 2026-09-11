import io
import unittest
from unittest.mock import patch

from scripts.check_urls import check_url


class FakeResponse:
    def __init__(self, status=200, content_type="application/vnd.apple.mpegurl", body=b"#EXTM3U\n"):
        self.status = status
        self.headers = {
            "Content-Type": content_type
        }
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, size=-1):
        return self.body


class TestCheckUrl(unittest.TestCase):

    @patch("scripts.check_urls.urllib.request.urlopen")
    def test_valid_m3u8(self, mock_urlopen):

        mock_urlopen.return_value = FakeResponse(
            status=200,
            content_type="application/vnd.apple.mpegurl",
            body=b"#EXTM3U\n#EXT-X-VERSION:3\n"
        )

        result = check_url(
            "https://example.com/test.m3u8"
        )

        self.assertEqual(
            result["status"],
            "online"
        )

        self.assertEqual(
            result["http_status"],
            200
        )

    @patch("scripts.check_urls.urllib.request.urlopen")
    def test_invalid_content(self, mock_urlopen):

        mock_urlopen.return_value = FakeResponse(
            status=200,
            content_type="text/html",
            body=b"<html>Hello</html>"
        )

        result = check_url(
            "https://example.com/test.m3u8"
        )

        self.assertEqual(
            result["status"],
            "invalid"
        )

        self.assertEqual(
            result["http_status"],
            200
        )

    @patch("scripts.check_urls.urllib.request.urlopen")
    def test_http_404(self, mock_urlopen):

        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com/test.m3u8",
            404,
            "Not Found",
            {},
            io.BytesIO()
        )

        result = check_url(
            "https://example.com/test.m3u8"
        )

        self.assertEqual(
            result["status"],
            "offline"
        )

        self.assertEqual(
            result["http_status"],
            404
        )


if __name__ == "__main__":
    unittest.main()