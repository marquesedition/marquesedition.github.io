#!/usr/bin/env python3

import html
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DATA_PATH = ROOT / "src" / "data" / "library.json"
PREVIEW_DIR = ROOT / "public" / "library-previews"
ROOT_FOLDER_ID = "1SpKqI5xXND6kUCdggTbjoRz4qywkuZjX"
SOURCE_URL = f"https://drive.google.com/drive/folders/{ROOT_FOLDER_ID}?usp=sharing"
USER_AGENT = "Mozilla/5.0"
REQUEST_DELAY_SECONDS = 0.04

ITEM_START_PATTERN = re.compile(r'\[\[null,"([^"]+)"\],null,null,null,"([^"]+)"')
ITEM_NAME_PATTERN = re.compile(r'\[\[16,null,\[null,\[\[\["(.*?)",null,true\]\]\]\]')
ITEM_DATE_PATTERN = re.compile(r'\[2,null,\[null,\[\[\["(.*?)"\]\]\]\]')
ITEM_SIZE_PATTERN = re.compile(r'\[1,null,\[null,\[\[\["(.*?)"\]\]\]\]')
TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HIDDEN_FILE_NAMES = {"icon", "thumbs.db", ".ds_store"}


def fetch_text(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text or "").strip()


def decode_drive_text(value):
    if not value:
        return ""

    def replace_unicode(match):
        return chr(int(match.group(1), 16))

    decoded = re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, value)
    decoded = decoded.replace("\\n", "\n").replace("\\r", "\r").replace('\\"', '"')
    decoded = decoded.replace("\\\\", "\\")
    return normalize_whitespace(decoded)


def read_balanced_array(document, start_index):
    depth = 0
    in_string = False
    escape = False

    for index in range(start_index, len(document)):
        char = document[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return document[start_index : index + 1]

    raise ValueError("No se pudo cerrar el array de un item de Google Drive.")


def extract_items(document):
    items = []
    seen_ids = set()

    for match in ITEM_START_PATTERN.finditer(document):
        item_id = match.group(1)
        if item_id in seen_ids:
            continue

        blob = read_balanced_array(document, match.start())
        name_match = ITEM_NAME_PATTERN.search(blob)
        raw_name = name_match.group(1) if name_match else ""
        name = decode_drive_text(raw_name)

        date_match = ITEM_DATE_PATTERN.search(blob)
        size_match = ITEM_SIZE_PATTERN.search(blob)

        item = {
            "id": item_id,
            "mime_type": match.group(2),
            "name": name,
            "modified_label": decode_drive_text(date_match.group(1) if date_match else ""),
            "size_label": decode_drive_text(size_match.group(1) if size_match else ""),
        }

        seen_ids.add(item_id)
        items.append(item)

    return items


def is_hidden_item(name):
    lowered = normalize_whitespace(name).lower()
    if not lowered:
        return True
    if lowered.startswith(".") or lowered.startswith("._"):
        return True
    return lowered in HIDDEN_FILE_NAMES


def parse_size_bytes(size_label):
    if not size_label or size_label == "—":
        return 0

    clean = size_label.replace("\xa0", " ").strip()
    match = re.match(r"([\d.,]+)\s*([KMGTP]?B)", clean, re.IGNORECASE)
    if not match:
        return 0

    value = float(match.group(1).replace(".", "").replace(",", "."))
    unit = match.group(2).upper()
    factors = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
        "PB": 1024**5,
    }
    return int(value * factors.get(unit, 1))


def format_size_bytes(size_bytes):
    if size_bytes <= 0:
        return ""

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"

    return f"{size:.1f}".replace(".", ",") + f" {units[unit_index]}"


def build_track(item):
    size_bytes = parse_size_bytes(item["size_label"])
    preview_path = PREVIEW_DIR / f"{item['id']}.mp3"

    return {
        "id": item["id"],
        "name": item["name"],
        "mime_type": item["mime_type"],
        "size_bytes": size_bytes,
        "size_label": item["size_label"] if item["size_label"] != "—" else "",
        "modified_label": item["modified_label"],
        "url": f"https://drive.google.com/file/d/{item['id']}/view?usp=sharing",
        "stream_url": f"https://drive.google.com/uc?export=download&id={item['id']}",
        "preview_url": f"/library-previews/{item['id']}.mp3",
        "preview_ready": preview_path.exists(),
    }


def crawl_folder(folder_id, name=None, visited=None):
    if visited is None:
        visited = set()

    if folder_id in visited:
        raise ValueError(f"Se detectó un bucle en la carpeta {folder_id}.")

    visited.add(folder_id)
    document = html.unescape(fetch_text(f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"))
    time.sleep(REQUEST_DELAY_SECONDS)

    items = extract_items(document)
    folders = []
    tracks = []

    for item in items:
        if is_hidden_item(item["name"]):
            continue

        if item["mime_type"] == "application/vnd.google-apps.folder":
            folders.append(crawl_folder(item["id"], item["name"], visited))
            continue

        if item["mime_type"].startswith("audio/"):
            tracks.append(build_track(item))

    title_match = TITLE_PATTERN.search(document)
    title = decode_drive_text(title_match.group(1)) if title_match else ""
    folder_name = name or title.replace(" - Google Drive", "").strip() or "Library"

    track_count = len(tracks) + sum(folder["track_count"] for folder in folders)
    folder_count = len(folders) + sum(folder["folder_count"] for folder in folders)
    total_size_bytes = sum(track["size_bytes"] for track in tracks) + sum(
        folder["total_size_bytes"] for folder in folders
    )

    visited.remove(folder_id)

    return {
        "id": folder_id,
        "name": folder_name,
        "url": f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing",
        "track_count": track_count,
        "folder_count": folder_count,
        "total_size_bytes": total_size_bytes,
        "total_size_label": format_size_bytes(total_size_bytes),
        "tracks": tracks,
        "folders": folders,
    }


def main():
    library = crawl_folder(ROOT_FOLDER_ID)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": SOURCE_URL,
        "root_folder_id": ROOT_FOLDER_ID,
        "library": library,
        "stats": {
            "folders": library["folder_count"],
            "tracks": library["track_count"],
            "total_size_bytes": library["total_size_bytes"],
            "total_size_label": library["total_size_label"],
        },
    }

    SOURCE_DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Library actualizada: {payload['stats']['folders']} carpetas, "
        f"{payload['stats']['tracks']} canciones, {payload['stats']['total_size_label'] or 'sin tamaño'}."
    )


if __name__ == "__main__":
    main()
