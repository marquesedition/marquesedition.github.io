#!/usr/bin/env python3

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE_USERNAME = "marquesedition"
PROFILE_URL = f"https://www.instagram.com/{PROFILE_USERNAME}/"
API_URL = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={PROFILE_USERNAME}"
FEED_API_URL = "https://www.instagram.com/api/v1/feed/user/{user_id}/"
OUTPUT_PATH = ROOT / "src" / "data" / "flyers.json"
FLYERS_DIR = ROOT / "public" / "flyers"
FEED_PAGE_SIZE = 50
MAX_FEED_PAGES = 8
PAGE_DELAY_SECONDS = 2

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "x-ig-app-id": "936619743392459",
    "x-requested-with": "XMLHttpRequest",
    "Referer": f"https://www.instagram.com/{PROFILE_USERNAME}/",
}

SEED_FLYERS = [
    {
        "shortcode": "DYZ3xTOKZ0r",
        "timestamp": 1778944616,
        "caption": "Esta noche Madrid se prende en Studio 54 Madrid.",
    },
    {
        "shortcode": "DYSaBiGqicM",
        "timestamp": 1778694197,
        "caption": "Este viernes la noche se viste de DISCO en Studio 54 Madrid.",
    },
    {
        "shortcode": "DYIRkUMis9m",
        "timestamp": 1778354282,
        "caption": "FIESTA NEON en Studio 54 Madrid.",
    },
]


def fetch_json(url):
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_profile_payload():
    return fetch_json(API_URL)


def fetch_profile_feed_items(user_id):
    items = []
    seen_codes = set()
    max_id = None
    complete = False

    for page_index in range(MAX_FEED_PAGES):
        params = {"count": str(FEED_PAGE_SIZE)}
        if max_id:
            params["max_id"] = max_id

        url = f"{FEED_API_URL.format(user_id=user_id)}?{urllib.parse.urlencode(params)}"
        payload = fetch_json(url)

        for item in payload.get("items", []):
            code = item.get("code")
            if code and code not in seen_codes:
                seen_codes.add(code)
                items.append(item)

        max_id = payload.get("next_max_id")
        if not payload.get("more_available") or not max_id:
            complete = True
            break

        if page_index < MAX_FEED_PAGES - 1:
            time.sleep(PAGE_DELAY_SECONDS)

    return items, complete


def load_existing_payload():
    if not OUTPUT_PATH.exists():
        return None

    return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def strip_hashtags(text):
    return re.sub(r"(?:^|\s)#[^\s#]+", "", text).strip()


def shorten(text, limit):
    clean = normalize_whitespace(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def is_flyer_item(item):
    if item.get("product_type") == "clips" or item.get("media_type") == 2:
        return False

    caption = (item.get("caption") or {}).get("text", "").lower()
    flyer_markers = (
        "studio 54",
        "studio54",
        "fiesta",
        "viernes",
        "sábado",
        "sabado",
        "noche",
        "disco",
        "neon",
        "party",
    )

    return any(marker in caption for marker in flyer_markers)


def derive_title(caption, shortcode):
    clean = strip_hashtags(caption)
    if not clean:
        return f"Flyer {shortcode}"

    first_line = next((line.strip() for line in clean.splitlines() if line.strip()), clean)
    first_line = re.sub(r"@[^\s]+", "", first_line).strip()
    return shorten(first_line, 64)


def derive_summary(caption):
    clean = strip_hashtags(caption)
    if not clean:
        return "Flyer de una fiesta realizada por Marques Edition."

    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    summary_source = " ".join(lines[:2]) if lines else clean
    return shorten(summary_source, 150)


def media_url(shortcode):
    return f"https://www.instagram.com/p/{shortcode}/media/?size=l"


def download_flyer_image(shortcode):
    FLYERS_DIR.mkdir(parents=True, exist_ok=True)
    target = FLYERS_DIR / f"{shortcode}.jpg"
    request = urllib.request.Request(
        media_url(shortcode),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": PROFILE_URL,
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        target.write_bytes(response.read())

    return f"/flyers/{target.name}"


def flyer_from_post(shortcode, timestamp, caption):
    caption = normalize_whitespace(caption)
    return {
        "shortcode": shortcode,
        "url": f"https://www.instagram.com/p/{shortcode}/",
        "image_url": download_flyer_image(shortcode),
        "date": datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat(),
        "timestamp": timestamp,
        "title": derive_title(caption, shortcode),
        "summary": derive_summary(caption),
        "venue": "Studio54 Madrid",
        "label": "Fiesta realizada",
        "caption": caption,
    }


def flyer_from_item(item):
    caption = (item.get("caption") or {}).get("text", "").strip()
    return flyer_from_post(item["code"], item["taken_at"], caption)


def build_payload(profile_payload):
    user = profile_payload["data"]["user"]
    items = []
    complete = False

    try:
        items, complete = fetch_profile_feed_items(user["id"])
    except Exception as exc:
        print(f"Instagram flyer feed refresh failed, using seed/cached flyers: {exc}", file=sys.stderr)

    flyers = []
    source = "instagram_feed"
    source_items_scanned = len(items)

    if items:
        for item in items:
            if is_flyer_item(item):
                try:
                    flyers.append(flyer_from_item(item))
                except Exception as exc:
                    print(f"Skipped flyer {item.get('code')}: {exc}", file=sys.stderr)
    else:
        source = "seed_flyers"
        for post in SEED_FLYERS:
            try:
                flyers.append(flyer_from_post(post["shortcode"], post["timestamp"], post["caption"]))
            except Exception as exc:
                print(f"Skipped seed flyer {post['shortcode']}: {exc}", file=sys.stderr)

    flyers = sorted(flyers, key=lambda flyer: flyer["timestamp"], reverse=True)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_profile": PROFILE_USERNAME,
        "source_url": PROFILE_URL,
        "source": source,
        "source_complete": complete,
        "source_items_scanned": source_items_scanned,
        "flyers": flyers,
    }


def remove_unused_images(flyers):
    keep_names = {Path(flyer["image_url"]).name for flyer in flyers}
    FLYERS_DIR.mkdir(parents=True, exist_ok=True)
    for path in FLYERS_DIR.glob("*"):
        if path.is_file() and path.name not in keep_names:
            path.unlink()


def main():
    existing_payload = load_existing_payload()

    try:
        profile_payload = fetch_profile_payload()
        payload = build_payload(profile_payload)
    except Exception as exc:
        is_rate_limit = isinstance(exc, urllib.error.HTTPError) and exc.code in {401, 429}
        is_temporary_network_error = isinstance(exc, urllib.error.URLError)

        if existing_payload and (is_rate_limit or is_temporary_network_error):
            print(
                f"Instagram flyers refresh skipped due to {exc}. Keeping cached data from {OUTPUT_PATH}.",
                file=sys.stderr,
            )
            print(f"Reused {len(existing_payload.get('flyers', []))} cached flyers from {OUTPUT_PATH}")
            return

        raise

    if not payload["flyers"] and existing_payload:
        print(
            "Instagram returned zero flyers. Keeping cached data instead of publishing an empty flyer list.",
            file=sys.stderr,
        )
        print(f"Reused {len(existing_payload.get('flyers', []))} cached flyers from {OUTPUT_PATH}")
        return

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    remove_unused_images(payload["flyers"])
    print(f"Wrote {len(payload['flyers'])} flyers to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to update flyers: {exc}", file=sys.stderr)
        raise
