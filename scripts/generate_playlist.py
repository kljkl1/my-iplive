import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "channels.json"
PLAYLIST_DIR = ROOT / "playlists"


def load_channels():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Channel data file not found: {DATA_FILE}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "channels.json must contain a JSON array."
        )

    return data


def validate_channel(channel):
    required_fields = [
        "id",
        "name",
        "url",
    ]

    for field in required_fields:
        if not channel.get(field):
            raise ValueError(
                f"Channel is missing required field: {field}"
            )


def safe_filename(value):
    """
    Convert category/country names into safe filenames.
    Example:
        News -> news
        Hong Kong -> hong-kong
    """
    value = str(value).strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value
    )

    value = value.strip("-")

    return value or "other"


def build_m3u(channels):
    lines = [
        "#EXTM3U"
    ]

    for channel in channels:
        validate_channel(channel)

        channel_id = channel["id"]
        name = channel["name"]
        url = channel["url"]

        country = channel.get(
            "country",
            ""
        )

        language = channel.get(
            "language",
            ""
        )

        category = channel.get(
            "category",
            "Other"
        )

        logo = channel.get(
            "logo",
            ""
        )

        extinf = (
            '#EXTINF:-1 '
            f'tvg-id="{channel_id}" '
            f'tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            f'group-title="{category}",'
            f'{name}'
        )

        lines.append(extinf)
        lines.append(url)

    return "\n".join(lines) + "\n"


def write_playlist(path, channels):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    content = build_m3u(channels)

    path.write_text(
        content,
        encoding="utf-8"
    )

    print(
        f"Generated: {path.relative_to(ROOT)} "
        f"({len(channels)} channels)"
    )


def generate_all_playlist(channels):
    output = PLAYLIST_DIR / "all.m3u"

    write_playlist(
        output,
        channels
    )


def generate_country_playlists(channels):
    groups = {}

    for channel in channels:
        country = channel.get(
            "country",
            "OTHER"
        )

        country_key = safe_filename(
            country
        )

        groups.setdefault(
            country_key,
            []
        ).append(channel)

    country_dir = (
        PLAYLIST_DIR / "country"
    )

    for country, country_channels in groups.items():

        output = (
            country_dir
            / f"{country}.m3u"
        )

        write_playlist(
            output,
            country_channels
        )


def generate_category_playlists(channels):
    groups = {}

    for channel in channels:
        category = channel.get(
            "category",
            "Other"
        )

        category_key = safe_filename(
            category
        )

        groups.setdefault(
            category_key,
            []
        ).append(channel)

    category_dir = (
        PLAYLIST_DIR / "category"
    )

    for category, category_channels in groups.items():

        output = (
            category_dir
            / f"{category}.m3u"
        )

        write_playlist(
            output,
            category_channels
        )


def main():
    print(
        "Loading channel database..."
    )

    channels = load_channels()

    print(
        f"Found {len(channels)} channels."
    )

    print()

    generate_all_playlist(
        channels
    )

    generate_country_playlists(
        channels
    )

    generate_category_playlists(
        channels
    )

    print()
    print(
        "All playlists generated successfully."
    )


if __name__ == "__main__":
    main()