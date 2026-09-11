import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = ROOT / "data" / "channels.json"


REQUIRED_FIELDS = [
    "id",
    "name",
    "url"
]


def validate_channels(data_file):
    print("Validating IPTV database...")
    print()

    data_file = Path(data_file)

    if not data_file.is_absolute():
        data_file = (Path.cwd() / data_file).resolve()

    if not data_file.exists():
        print(f"ERROR: File not found: {data_file}")
        sys.exit(1)

    try:
        with open(
            data_file,
            "r",
            encoding="utf-8"
        ) as file:
            channels = json.load(file)

    except json.JSONDecodeError as error:
        print("ERROR: Invalid JSON")
        print(error)
        sys.exit(1)

    if not isinstance(channels, list):
        print(
            "ERROR: channels.json must contain a list."
        )
        sys.exit(1)

    ids = set()

    for index, channel in enumerate(
        channels,
        start=1
    ):
        if not isinstance(channel, dict):
            print(
                f"ERROR: Channel #{index} "
                f"must be an object."
            )
            sys.exit(1)

        for field in REQUIRED_FIELDS:
            if not channel.get(field):
                print(
                    f"ERROR: Channel #{index} "
                    f"is missing '{field}'"
                )
                sys.exit(1)

        channel_id = channel["id"]

        if channel_id in ids:
            print(
                f"ERROR: Duplicate channel ID: "
                f"{channel_id}"
            )
            sys.exit(1)

        ids.add(channel_id)

    try:
        display_path = data_file.relative_to(ROOT)
    except ValueError:
        display_path = data_file

    print(
        f"File: {display_path}"
    )

    print(
        f"Channels: {len(channels)}"
    )

    print(
        f"Unique IDs: {len(ids)}"
    )

    print()
    print("Validation PASSED.")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate IPTV channel database."
        )
    )

    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_DATA_FILE,
        help=(
            "JSON channel database to validate "
            "(default: data/channels.json)"
        )
    )

    args = parser.parse_args()

    try:
        validate_channels(
            args.input
        )
    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError
    ) as error:
        print(
            f"ERROR: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
