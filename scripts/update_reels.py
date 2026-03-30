#!/usr/bin/env python3

import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROFILE_USERNAME = "marquesedition"
PROFILE_URL = f"https://www.instagram.com/{PROFILE_USERNAME}/reels/"
API_URL = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={PROFILE_USERNAME}"
OUTPUT_PATH = Path("media-links/reels.json")
SOURCE_DATA_PATH = Path("src/data/reels.json")
THUMBNAILS_DIR = Path("public/reel-thumbs")


def fetch_profile_payload():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


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
    if "pensionmimosas" in lowered or "@pensionmimosas" in lowered:
        return "Pension Mimosas"
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


def clear_existing_thumbnails():
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
    for path in THUMBNAILS_DIR.glob("*"):
        if path.is_file():
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


def reel_from_node(node):
    caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
    caption = ""
    if caption_edges:
        caption = caption_edges[0].get("node", {}).get("text", "").strip()

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


def build_reels_payload(profile_payload):
    user = profile_payload["data"]["user"]
    edges = user["edge_owner_to_timeline_media"]["edges"]
    reels = []

    for edge in edges:
        node = edge["node"]
        if node.get("product_type") == "clips" and node.get("is_video"):
            reels.append(reel_from_node(node))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_profile": PROFILE_USERNAME,
        "source_url": PROFILE_URL,
        "profile": {
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "category": user.get("category_name", ""),
            "bio": user.get("biography", ""),
            "followers": user.get("edge_followed_by", {}).get("count", 0),
            "following": user.get("edge_follow", {}).get("count", 0),
            "posts": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
            "highlights": user.get("highlight_reel_count", 0),
        },
        "reels": reels,
    }


def main():
    payload = fetch_profile_payload()
    clear_existing_thumbnails()
    reels_payload = build_reels_payload(payload)

    payload_json = json.dumps(reels_payload, ensure_ascii=False, indent=2) + "\n"
    OUTPUT_PATH.write_text(payload_json, encoding="utf-8")
    SOURCE_DATA_PATH.write_text(payload_json, encoding="utf-8")

    print(f"Wrote {len(reels_payload['reels'])} reels to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to update reels: {exc}", file=sys.stderr)
        raise
