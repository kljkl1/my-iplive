import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "channels.json"
STATUS_FILE = ROOT / "data" / "status.json"

TIMEOUT_SECONDS = 10


def load_channels():
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

    return channels


def check_url(url):
    start_time = time.perf_counter()

    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "my-iplive-url-checker/1.0",
            "Accept": (
                "application/vnd.apple.mpegurl,"
                "application/x-mpegURL,"
                "application/octet-stream,"
                "*/*"
            )
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=TIMEOUT_SECONDS
        ) as response:

            elapsed_ms = round(
                (time.perf_counter() - start_time) * 1000
            )

            http_status = response.status

            if not (200 <= http_status < 300):
                return {
                    "status": "offline",
                    "http_status": http_status,
                    "response_time_ms": elapsed_ms,
                    "content_type": response.headers.get(
                        "Content-Type"
                    ),
                    "error": (
                        f"Unexpected HTTP status: "
                        f"{http_status}"
                    )
                }

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            content_type = content_type.lower()

            body = response.read(64 * 1024)

            try:
                text = body.decode(
                    "utf-8",
                    errors="ignore"
                )
            except Exception:
                text = ""

            if "#EXTM3U" not in text:
                return {
                    "status": "invalid",
                    "http_status": http_status,
                    "response_time_ms": elapsed_ms,
                    "content_type": content_type,
                    "error": (
                        "Response does not contain "
                        "#EXTM3U"
                    )
                }

            return {
                "status": "online",
                "http_status": http_status,
                "response_time_ms": elapsed_ms,
                "content_type": content_type,
                "error": None
            }

    except urllib.error.HTTPError as error:

        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "status": "offline",
            "http_status": error.code,
            "response_time_ms": elapsed_ms,
            "content_type": (
                error.headers.get("Content-Type")
                if error.headers
                else None
            ),
            "error": str(error)
        }

    except urllib.error.URLError as error:

        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "status": "offline",
            "http_status": None,
            "response_time_ms": elapsed_ms,
            "content_type": None,
            "error": str(error.reason)
        }

    except TimeoutError:

        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "status": "offline",
            "http_status": None,
            "response_time_ms": elapsed_ms,
            "content_type": None,
            "error": "Connection timed out"
        }

    except Exception as error:

        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "status": "offline",
            "http_status": None,
            "response_time_ms": elapsed_ms,
            "content_type": None,
            "error": str(error)
        }


def build_status(channels):
    updated_at = datetime.now(
        timezone.utc
    ).isoformat()

    result = {
        "updated_at": updated_at,
        "channels": {}
    }

    for index, channel in enumerate(
        channels,
        start=1
    ):
        channel_id = channel.get("id")
        url = channel.get("url")

        if not channel_id:
            raise ValueError(
                f"Channel #{index} is missing 'id'."
            )

        if not url:
            raise ValueError(
                f"Channel '{channel_id}' "
                f"is missing 'url'."
            )

        print(
            f"Checking {channel_id}..."
        )
        print(
            f"  URL: {url}"
        )

        status = check_url(url)

        result["channels"][channel_id] = status

        print(
            f"  Status: {status['status']}"
        )
        print(
            f"  HTTP: {status['http_status']}"
        )
        print(
            f"  Response: "
            f"{status['response_time_ms']} ms"
        )

        if status["error"]:
            print(
                f"  Error: {status['error']}"
            )

        print()

    return result


def save_status(status):
    STATUS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        STATUS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            status,
            file,
            ensure_ascii=False,
            indent=2
        )

        file.write("\n")


def main():
    print("Starting IPTV URL health check...")
    print()

    try:
        channels = load_channels()

        print(
            f"Found {len(channels)} channels."
        )
        print()

        status = build_status(
            channels
        )

        save_status(
            status
        )

    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError
    ) as error:

        print()
        print(
            f"ERROR: {error}"
        )
        print()
        print(
            "URL health check FAILED."
        )

        sys.exit(1)

    print(
        f"Status written to: "
        f"{STATUS_FILE.relative_to(ROOT)}"
    )

    print()
    print(
        "URL health check completed."
    )


if __name__ == "__main__":
    main()