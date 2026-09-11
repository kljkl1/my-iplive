import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "channels.json"
EPG_FILE = ROOT / "epg" / "epg.xml"


def load_channel_ids():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Channel data file not found: {DATA_FILE}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        channels = json.load(file)

    if not isinstance(channels, list):
        raise ValueError(
            "channels.json must contain a JSON array."
        )

    channel_ids = set()

    for channel in channels:
        channel_id = channel.get("id")

        if not channel_id:
            raise ValueError(
                "A channel in channels.json is missing 'id'."
            )

        if channel_id in channel_ids:
            raise ValueError(
                f"Duplicate channel ID: {channel_id}"
            )

        channel_ids.add(channel_id)

    return channel_ids


def parse_xml():
    if not EPG_FILE.exists():
        raise FileNotFoundError(
            f"EPG file not found: {EPG_FILE}"
        )

    try:
        tree = ET.parse(EPG_FILE)
    except ET.ParseError as error:
        raise ValueError(
            f"Invalid XML: {error}"
        )

    root = tree.getroot()

    if root.tag != "tv":
        raise ValueError(
            "EPG root element must be <tv>."
        )

    return root


def parse_xmltv_time(value):
    """
    Parse XMLTV time format such as:
    20260911200000 +0000
    """

    if not value:
        raise ValueError(
            "Programme time value is empty."
        )

    try:
        return datetime.strptime(
            value,
            "%Y%m%d%H%M%S %z"
        )
    except ValueError:
        raise ValueError(
            f"Invalid XMLTV time: {value}"
        )


def validate_channels(root, database_ids):
    epg_ids = set()

    channels = root.findall("channel")

    if not channels:
        raise ValueError(
            "EPG contains no <channel> elements."
        )

    for channel in channels:
        channel_id = channel.get("id")

        if not channel_id:
            raise ValueError(
                "An EPG channel is missing 'id'."
            )

        if channel_id in epg_ids:
            raise ValueError(
                f"Duplicate EPG channel ID: {channel_id}"
            )

        if channel_id not in database_ids:
            raise ValueError(
                f"EPG channel '{channel_id}' "
                f"does not exist in channels.json."
            )

        display_name = channel.find("display-name")

        if display_name is None:
            raise ValueError(
                f"EPG channel '{channel_id}' "
                f"is missing <display-name>."
            )

        epg_ids.add(channel_id)

    return epg_ids


def validate_programmes(root, epg_ids):
    programmes = root.findall("programme")

    if not programmes:
        raise ValueError(
            "EPG contains no <programme> elements."
        )

    for index, programme in enumerate(
        programmes,
        start=1
    ):
        channel_id = programme.get("channel")

        if not channel_id:
            raise ValueError(
                f"Programme #{index} is missing "
                f"'channel'."
            )

        if channel_id not in epg_ids:
            raise ValueError(
                f"Programme #{index} references "
                f"unknown channel '{channel_id}'."
            )

        start = programme.get("start")
        stop = programme.get("stop")

        if not start:
            raise ValueError(
                f"Programme #{index} is missing "
                f"'start'."
            )

        if not stop:
            raise ValueError(
                f"Programme #{index} is missing "
                f"'stop'."
            )

        start_time = parse_xmltv_time(start)
        stop_time = parse_xmltv_time(stop)

        if start_time >= stop_time:
            raise ValueError(
                f"Programme #{index} has invalid "
                f"time range: start >= stop."
            )

        title = programme.find("title")

        if title is None or not title.text:
            raise ValueError(
                f"Programme #{index} is missing "
                f"<title>."
            )

    return len(programmes)


def main():
    print("Validating EPG...")
    print()

    try:
        database_ids = load_channel_ids()

        print(
            f"Database channels: {len(database_ids)}"
        )

        root = parse_xml()

        epg_ids = validate_channels(
            root,
            database_ids
        )

        print(
            f"EPG channels: {len(epg_ids)}"
        )

        programme_count = validate_programmes(
            root,
            epg_ids
        )

        print(
            f"Programmes: {programme_count}"
        )

    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError
    ) as error:

        print()
        print(f"ERROR: {error}")
        print()
        print("EPG validation FAILED.")

        sys.exit(1)

    print()
    print("EPG validation PASSED.")


if __name__ == "__main__":
    main()