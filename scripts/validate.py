import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "channels.json"


REQUIRED_FIELDS = [
    "id",
    "name",
    "url"
]


def main():
    print("Validating IPTV database...")
    print()

    if not DATA_FILE.exists():
        print(f"ERROR: File not found: {DATA_FILE}")
        sys.exit(1)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            channels = json.load(file)
    except json.JSONDecodeError as error:
        print("ERROR: Invalid JSON")
        print(error)
        sys.exit(1)

    if not isinstance(channels, list):
        print("ERROR: channels.json must contain a list.")
        sys.exit(1)

    ids = set()

    for index, channel in enumerate(channels, start=1):

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
                f"ERROR: Duplicate channel ID: {channel_id}"
            )
            sys.exit(1)

        ids.add(channel_id)

    print(f"Channels: {len(channels)}")
    print(f"Unique IDs: {len(ids)}")
    print()
    print("Validation PASSED.")


if __name__ == "__main__":
    main()