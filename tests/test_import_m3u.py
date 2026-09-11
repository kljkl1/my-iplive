import tempfile
import unittest
from pathlib import Path

from scripts.import_m3u import (
    parse_m3u,
    validate_channels,
)


class TestImportM3U(unittest.TestCase):

    def create_m3u(self, content, encoding="utf-8"):
        temp_dir = tempfile.TemporaryDirectory()
        file_path = Path(temp_dir.name) / "test.m3u"

        file_path.write_text(
            content,
            encoding=encoding
        )

        return temp_dir, file_path

    def test_standard_m3u(self):
        content = """#EXTM3U
#EXTINF:-1 tvg-id="demo-news" tvg-name="Demo News" tvg-logo="https://example.com/news.png" group-title="News",Demo News
https://example.com/news.m3u8
#EXTINF:-1 tvg-id="demo-sports" tvg-name="Demo Sports" group-title="Sports",Demo Sports
https://example.com/sports.m3u8
"""

        temp_dir, file_path = self.create_m3u(content)

        try:
            channels = parse_m3u(file_path)

            self.assertEqual(
                len(channels),
                2
            )

            self.assertEqual(
                channels[0]["id"],
                "demo-news"
            )

            self.assertEqual(
                channels[0]["name"],
                "Demo News"
            )

            self.assertEqual(
                channels[0]["category"],
                "News"
            )

            self.assertEqual(
                channels[0]["url"],
                "https://example.com/news.m3u8"
            )

            validate_channels(channels)

        finally:
            temp_dir.cleanup()

    def test_auto_generate_id(self):
        content = """#EXTM3U
#EXTINF:-1 group-title="News",Example Channel
https://example.com/example.m3u8
"""

        temp_dir, file_path = self.create_m3u(content)

        try:
            channels = parse_m3u(file_path)

            self.assertEqual(
                len(channels),
                1
            )

            self.assertEqual(
                channels[0]["id"],
                "example-channel"
            )

        finally:
            temp_dir.cleanup()

    def test_duplicate_id(self):
        content = """#EXTM3U
#EXTINF:-1 tvg-id="duplicate",Channel One
https://example.com/one.m3u8
#EXTINF:-1 tvg-id="duplicate",Channel Two
https://example.com/two.m3u8
"""

        temp_dir, file_path = self.create_m3u(content)

        try:
            channels = parse_m3u(file_path)

            with self.assertRaises(ValueError):
                validate_channels(channels)

        finally:
            temp_dir.cleanup()

    def test_missing_url(self):
        content = """#EXTM3U
#EXTINF:-1 tvg-id="missing-url",Missing URL
"""

        temp_dir, file_path = self.create_m3u(content)

        try:
            with self.assertRaises(ValueError):
                parse_m3u(file_path)

        finally:
            temp_dir.cleanup()

    def test_invalid_m3u_header(self):
        content = """NOT-M3U
#EXTINF:-1,Invalid Playlist
https://example.com/test.m3u8
"""

        temp_dir, file_path = self.create_m3u(content)

        try:
            with self.assertRaises(ValueError):
                parse_m3u(file_path)

        finally:
            temp_dir.cleanup()

    def test_utf8_bom(self):
        content = """#EXTM3U
#EXTINF:-1 tvg-id="bom-test",BOM Test
https://example.com/bom.m3u8
"""

        temp_dir, file_path = self.create_m3u(
            content,
            encoding="utf-8-sig"
        )

        try:
            channels = parse_m3u(file_path)

            self.assertEqual(
                len(channels),
                1
            )

            self.assertEqual(
                channels[0]["id"],
                "bom-test"
            )

        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()