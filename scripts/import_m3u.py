import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DEFAULT_OUTPUT = ROOT / "data" / "channels.json"


ATTRIBUTE_PATTERN = re.compile(
    r'([\w-]+)="([^"]*)"'
)


def parse_attributes(extinf_line):
    return dict(
        ATTRIBUTE_PATTERN.findall(extinf_line)
    )


def make_channel_id(attributes, name, index):
    channel_id = attributes.get("tvg-id")

    if channel_id:
        return channel_id.strip()

    normalized = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        name.strip().lower()
    ).strip("-")

    if normalized:
        return normalized

    return f"channel-{index}"


def parse_group(group):
    if not group:
        return "Uncategorized"

    group = group.strip()

    if not group:
        return "Uncategorized"

    return group


def parse_m3u(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"M3U file not found: {file_path}"
        )

    try:
        content = file_path.read_text(
            encoding="utf-8-sig"
        )
    except UnicodeDecodeError:
        content = file_path.read_text(
            encoding="utf-8",
            errors="replace"
        )

    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    if not lines:
        raise ValueError(
            "M3U file is empty."
        )

    if not lines[0].upper().startswith("#EXTM3U"):
        raise ValueError(
            "Input file does not start with #EXTM3U."
        )

    channels = []

    index = 0
    position = 1

    while position < len(lines):

        line = lines[position]

        if not line.upper().startswith("#EXTINF:"):
            position += 1
            continue

        extinf = line

        if "," not in extinf:
            raise ValueError(
                f"Invalid #EXTINF line near "
                f"entry #{index + 1}."
            )

        metadata, display_name = extinf.split(
            ",",
            1
        )

        attributes = parse_attributes(
            metadata
        )

        display_name = display_name.strip()

        if not display_name:
            raise ValueError(
                f"Channel #{index + 1} "
                f"has an empty name."
            )

        url = None

        next_position = position + 1

        while next_position < len(lines):

            candidate = lines[next_position]

            if candidate.startswith("#"):
                next_position += 1
                continue

            url = candidate
            break

        if not url:
            raise ValueError(
                f"Channel '{display_name}' "
                f"is missing a URL."
            )

        index += 1

        channel = {
            "id": make_channel_id(
                attributes,
                display_name,
                index
            ),
            "name": attributes.get(
                "tvg-name",
                display_name
            ).strip(),
            "country": attributes.get(
                "country",
                ""
            ).strip(),
            "language": attributes.get(
                "language",
                ""
            ).strip(),
            "category": parse_group(
                attributes.get(
                    "group-title",
                    ""
                )
            ),
            "logo": attributes.get(
                "tvg-logo",
                ""
            ).strip(),
            "url": url
        }

        channels.append(channel)

        position = next_position + 1

    if not channels:
        raise ValueError(
            "No #EXTINF channel entries found."
        )

    return channels


def validate_channels(channels):
    ids = set()

    for index, channel in enumerate(
        channels,
        start=1
    ):
        channel_id = channel.get("id")

        if not channel_id:
            raise ValueError(
                f"Channel #{index} is missing ID."
            )

        if channel_id in ids:
            raise ValueError(
                f"Duplicate channel ID: "
                f"{channel_id}"
            )

        ids.add(channel_id)

        if not channel.get("name"):
            raise ValueError(
                f"Channel #{index} is missing name."
            )

        if not channel.get("url"):
            raise ValueError(
                f"Channel '{channel_id}' "
                f"is missing URL."
            )


def save_channels(channels, output_file):
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            channels,
            file,
            ensure_ascii=False,
            indent=2
        )

        file.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Import a standard M3U playlist "
            "into channels.json format."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input M3U file"
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "Output JSON file "
            "(default: data/channels.json)"
        )
    )

    args = parser.parse_args()

    print("M3U importer")
    print()

    try:
        channels = parse_m3u(
            args.input
        )

        validate_channels(
            channels
        )

        save_channels(
            channels,
            args.output
        )

    except (
        FileNotFoundError,
        ValueError
    ) as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    print(
        f"Imported channels: "
        f"{len(channels)}"
    )

    print(
        f"Output: "
        f"{args.output}"
    )

    print()
    print(
        "M3U import completed successfully."
    )


if __name__ == "__main__":
    main()