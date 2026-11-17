import json
import re
import sys
import urllib.request
from pathlib import Path

UPSTREAMS = (
    "https://data.17500.cn/3d_asc.txt",
    "http://data.17500.cn/3d_asc.txt",
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://data.17500.cn/",
    "Accept": "text/plain,*/*",
}

ROW_PATTERN = re.compile(r"^\d{7}\s+\d{4}-\d{2}-\d{2}\s")
COLUMN_COUNT = 17
MIN_ROWS = 100
MAX_ATTEMPTS = 2
TIMEOUT = 30
OUTPUT = Path("3d_data.js")
WRAPPER = "window.__FC3D_TEXT__"


def fetch(url: str) -> list[str]:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        text = response.read().decode("utf-8", errors="replace")
    rows = [
        line.strip()
        for line in text.splitlines()
        if ROW_PATTERN.match(line.strip())
        and len(line.strip().split()) == COLUMN_COUNT
    ]
    if len(rows) < MIN_ROWS:
        raise RuntimeError(f"too few valid rows: {len(rows)}")
    return rows


def load_rows() -> list[str]:
    last_error: Exception | None = None
    for url in UPSTREAMS:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return fetch(url)
            except Exception as exc:
                last_error = exc
                print(f"{url} attempt {attempt} failed: {exc}")
    raise RuntimeError(f"all upstreams failed: {last_error}")


def validate(rows: list[str]) -> None:
    for previous, current in zip(rows, rows[1:]):
        previous_id = int(previous.split()[0])
        current_id = int(current.split()[0])
        if current_id <= previous_id:
            raise RuntimeError(
                f"issue numbers not increasing: {previous_id} -> {current_id}"
            )


def write(rows: list[str]) -> None:
    payload = "\n".join(rows) + "\n"
    OUTPUT.write_text(
        f"{WRAPPER} = {json.dumps(payload, ensure_ascii=False)};\n",
        encoding="utf-8",
    )


def main() -> int:
    rows = load_rows()
    validate(rows)
    write(rows)
    print(f"wrote {OUTPUT} | rows={len(rows)} | latest={rows[-1][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
