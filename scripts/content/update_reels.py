#!/usr/bin/env python3

import html
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
PROFILE_URL = f"https://www.instagram.com/{PROFILE_USERNAME}/reels/"
API_URL = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={PROFILE_USERNAME}"
FEED_API_URL = "https://www.instagram.com/api/v1/feed/user/{user_id}/"
SOURCE_DATA_PATH = ROOT / "src" / "data" / "reels.json"
THUMBNAILS_DIR = ROOT / "public" / "reel-thumbs"
FEED_PAGE_SIZE = 50
MAX_FEED_PAGES = 8
PAGE_DELAY_SECONDS = 2

LEGACY_HANDLE = "pension" + "mimosas"
LEGACY_VENUE_ES = "Pensi" + "\u00f3n " + "Mimosas"
LEGACY_VENUE_ASCII = "Pension " + "Mimosas"
LEGACY_HASHTAG = "Pension" + "Mimosas"

VENUE_TEXT_REPLACEMENTS = (
    (LEGACY_VENUE_ES, "Studio54 Madrid"),
    (LEGACY_VENUE_ASCII, "Studio54 Madrid"),
    (LEGACY_HASHTAG, "Studio54Madrid"),
    (LEGACY_HANDLE, "studio54_madrid"),
)


REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "x-ig-app-id": "936619743392459",
    "x-requested-with": "XMLHttpRequest",
    "Referer": f"https://www.instagram.com/{PROFILE_USERNAME}/",
}


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers=REQUEST_HEADERS,
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_profile_payload():
    return fetch_json(API_URL)


def load_existing_payload():
    if not SOURCE_DATA_PATH.exists():
        return None

    return json.loads(SOURCE_DATA_PATH.read_text(encoding="utf-8"))


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def normalize_venue_references(text):
    clean = text
    for old_value, new_value in VENUE_TEXT_REPLACEMENTS:
        clean = clean.replace(old_value, new_value)
    return clean


def strip_hashtags(text):
    return re.sub(r"(?:^|\s)#[^\s#]+", "", text).strip()


def shorten(text, limit):
    clean = normalize_whitespace(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def is_title_candidate(line):
    candidate = strip_hashtags(line)
    candidate = re.sub(r"@[^\s]+", "", candidate).strip()
    if re.search(r"\d{1,2}:\d{2}", candidate):
        return False

    letters = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", "", candidate)
    return len(letters) >= 4


def derive_title(lines, shortcode):
    if not lines:
        return f"Reel {shortcode}"

    for line in lines:
        if is_title_candidate(line):
            return shorten(strip_hashtags(line) or line, 56)

    return shorten(strip_hashtags(lines[0]) or lines[0], 56)


def derive_summary(lines):
    if not lines:
        return "Reel de Marques Edition en cabina."

    summary_source = " ".join(lines[1:3]) if len(lines) > 1 else lines[0]
    summary_source = strip_hashtags(summary_source) or lines[0]
    return shorten(summary_source, 140)


def derive_label(caption):
    lowered = caption.lower()
    if "boda" in lowered or "wedding" in lowered:
        return "Boda"
    if "residente" in lowered or "resident" in lowered:
        return "DJ residente"
    if "studio54" in lowered or "studio54_madrid" in lowered:
        return "Studio54 Madrid"
    if "mix" in lowered or "mashup" in lowered:
        return "Mezcla"
    return "Reel"


def fetch_binary(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.instagram.com/",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def remove_unused_thumbnails(reels):
    keep_names = {f"{reel['shortcode']}.jpg" for reel in reels}
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
    for path in THUMBNAILS_DIR.glob("*"):
        if path.is_file() and path.name not in keep_names:
            path.unlink()


def store_thumbnail(shortcode, thumbnail_url):
    if not thumbnail_url:
        return ""

    target = THUMBNAILS_DIR / f"{shortcode}.jpg"
    try:
        target.write_bytes(fetch_binary(thumbnail_url))
        return f"/reel-thumbs/{target.name}"
    except Exception:
        return ""


def is_reel_item(item):
    return item.get("product_type") == "clips" or bool(item.get("clips_metadata"))


def thumbnail_from_feed_item(item):
    candidates = item.get("image_versions2", {}).get("candidates", [])
    if candidates:
        return candidates[0].get("url", "")
    return item.get("thumbnail_url", "")


def reel_from_feed_item(item):
    caption = (item.get("caption") or {}).get("text", "").strip()
    caption = normalize_venue_references(caption)

    lines = [line.strip() for line in caption.splitlines() if line.strip()]
    shortcode = item["code"]
    timestamp = item["taken_at"]
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()

    return {
        "shortcode": shortcode,
        "url": f"https://www.instagram.com/reel/{shortcode}/",
        "date": date,
        "timestamp": timestamp,
        "thumbnail_url": store_thumbnail(shortcode, thumbnail_from_feed_item(item)),
        "view_count": item.get("play_count") or item.get("view_count") or item.get("ig_play_count") or 0,
        "title": derive_title(lines, shortcode),
        "summary": derive_summary(lines),
        "label": derive_label(caption),
        "caption": caption,
    }


def reel_from_node(node):
    caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
    caption = ""
    if caption_edges:
        caption = caption_edges[0].get("node", {}).get("text", "").strip()
        caption = normalize_venue_references(caption)

    lines = [line.strip() for line in caption.splitlines() if line.strip()]
    shortcode = node["shortcode"]
    timestamp = node["taken_at_timestamp"]
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
    thumbnail_url = node.get("thumbnail_src") or node.get("display_url", "")

    return {
        "shortcode": shortcode,
        "url": f"https://www.instagram.com/reel/{shortcode}/",
        "date": date,
        "timestamp": timestamp,
        "thumbnail_url": store_thumbnail(shortcode, thumbnail_url),
        "view_count": node.get("video_view_count", 0),
        "title": derive_title(lines, shortcode),
        "summary": derive_summary(lines),
        "label": derive_label(caption),
        "caption": caption,
    }


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

        try:
            payload = fetch_json(url)
        except Exception as exc:
            if items:
                print(
                    f"Instagram feed pagination stopped after {len(items)} items: {exc}",
                    file=sys.stderr,
                )
                break
            raise

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


def fallback_reels_from_profile_payload(profile_payload):
    edges = profile_payload["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
    reels = []

    for edge in edges:
        node = edge["node"]
        if node.get("product_type") == "clips" and node.get("is_video"):
            reels.append(reel_from_node(node))

    return reels


def build_reels_payload(profile_payload):
    user = profile_payload["data"]["user"]
    feed_items = []
    feed_complete = False

    try:
        feed_items, feed_complete = fetch_profile_feed_items(user["id"])
    except Exception as exc:
        print(f"Instagram feed refresh failed, using web profile fallback: {exc}", file=sys.stderr)

    if feed_items:
        reels = [reel_from_feed_item(item) for item in feed_items if is_reel_item(item)]
    else:
        reels = fallback_reels_from_profile_payload(profile_payload)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_profile": PROFILE_USERNAME,
        "source_url": PROFILE_URL,
        "source_complete": feed_complete,
        "source_items_scanned": len(feed_items),
        "profile": {
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "category": user.get("category_name", ""),
            "bio": normalize_venue_references(user.get("biography", "")),
            "followers": user.get("edge_followed_by", {}).get("count", 0),
            "following": user.get("edge_follow", {}).get("count", 0),
            "posts": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
            "highlights": user.get("highlight_reel_count", 0),
        },
        "reels": reels,
    }


def main():
    existing_payload = load_existing_payload()

    try:
        payload = fetch_profile_payload()
    except Exception as exc:
        is_rate_limit = isinstance(exc, urllib.error.HTTPError) and exc.code in {401, 429}
        is_temporary_network_error = isinstance(exc, urllib.error.URLError)

        if existing_payload and (is_rate_limit or is_temporary_network_error):
            reason = f"HTTP {exc.code} rate limit" if is_rate_limit else f"temporary network error: {exc}"
            print(
                f"Instagram reels refresh skipped due to {reason}. Keeping cached data from {SOURCE_DATA_PATH}.",
                file=sys.stderr,
            )
            print(
                f"Reused {len(existing_payload.get('reels', []))} cached reels from {SOURCE_DATA_PATH}"
            )
            return

        raise

    reels_payload = build_reels_payload(payload)
    if not reels_payload["reels"] and existing_payload:
        print(
            "Instagram returned zero reels. Keeping cached data instead of publishing an empty reel list.",
            file=sys.stderr,
        )
        print(f"Reused {len(existing_payload.get('reels', []))} cached reels from {SOURCE_DATA_PATH}")
        return
    if (
        not reels_payload["source_complete"]
        and existing_payload
        and len(existing_payload.get("reels", [])) > len(reels_payload["reels"])
    ):
        reels_payload["reels"] = existing_payload["reels"]
        reels_payload["source_complete"] = existing_payload.get("source_complete", False)
        reels_payload["source_items_scanned"] = existing_payload.get(
            "source_items_scanned",
            reels_payload["source_items_scanned"],
        )
        reels_payload["source_note"] = "Kept cached reels after a partial Instagram refresh."
        print(
            "Instagram returned a partial reel list. Keeping the larger cached reel list while updating profile stats.",
            file=sys.stderr,
        )

    payload_json = json.dumps(reels_payload, ensure_ascii=False, indent=2) + "\n"
    SOURCE_DATA_PATH.write_text(payload_json, encoding="utf-8")
    remove_unused_thumbnails(reels_payload["reels"])

    status = "complete" if reels_payload["source_complete"] else "partial"
    print(
        f"Wrote {len(reels_payload['reels'])} reels to {SOURCE_DATA_PATH} "
        f"({status}, scanned {reels_payload['source_items_scanned']} Instagram items)"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to update reels: {exc}", file=sys.stderr)
        raise
