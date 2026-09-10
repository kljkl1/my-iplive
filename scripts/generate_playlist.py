import json
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
        raise ValueError("channels.json must contain a JSON array.")

    return data


def validate_channel(channel):
    required_fields = [
        "id",
        "name",
        "url"
    ]

    for field in required_fields:
        if not channel.get(field):
            raise ValueError(
                f"Channel is missing required field: {field}"
            )


def build_m3u(channels):
    lines = [
        "#EXTM3U"
    ]

    for channel in channels:
        validate_channel(channel)

        channel_id = channel["id"]
        name = channel["name"]
        url = channel["url"]

        country = channel.get("country", "")
        language = channel.get("language", "")
        category = channel.get("category", "Other")
        logo = channel.get("logo", "")

        extinf = (
            '#EXTINF:-1 '
            f'tvg-id="{channel_id}" '
            f'tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            f'group-title="{category}" '
            f'country="{country}" '
            f'language="{language}",'
            f'{name}'
        )

        lines.append(extinf)
        lines.append(url)

    return "\n".join(lines) + "\n"


def main():
    print("Loading channel database...")

    channels = load_channels()

    print(f"Found {len(channels)} channels.")

    PLAYLIST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    playlist = build_m3u(channels)

    output_file = PLAYLIST_DIR / "all.m3u"

    output_file.write_text(
        playlist,
        encoding="utf-8"
    )

    print()
    print("Playlist generated successfully.")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()