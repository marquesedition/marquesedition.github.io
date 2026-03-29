#!/usr/bin/env python3

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


CHANNEL_HANDLE = "@marquesedition"
CHANNEL_URL = f"https://www.youtube.com/{CHANNEL_HANDLE}"
STREAMS_URL = f"{CHANNEL_URL}/streams"
SOURCE_URL = f"{STREAMS_URL}?ucbcb=1"
OUTPUT_PATH = Path("media-links/streams.json")
SOURCE_DATA_PATH = Path("src/data/streams.json")
USER_AGENT = "Mozilla/5.0"


def fetch_text(url, data=None, headers=None):
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(url, data=data, headers=request_headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def fetch_json(url, payload, headers=None):
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if headers:
        request_headers.update(headers)

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=request_headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text or "").strip()


def shorten(text, limit):
    clean = normalize_whitespace(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def text_from_runs(value):
    if not value:
        return ""
    if "simpleText" in value:
        return normalize_whitespace(value["simpleText"])
    return normalize_whitespace("".join(run.get("text", "") for run in value.get("runs", [])))


def parse_number(value):
    digits = re.sub(r"[^\d]", "", value or "")
    return int(digits) if digits else 0


def extract_first_json_string(document, pattern):
    match = re.search(pattern, document)
    if not match:
        return None
    return json.loads(f'"{match.group(1)}"')


def extract_json_assignment(document, marker):
    marker_index = document.find(marker)
    if marker_index == -1:
        raise ValueError(f"Marker not found: {marker}")

    start = document.find("{", marker_index)
    if start == -1:
        raise ValueError(f"JSON start not found after marker: {marker}")

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(document)):
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
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(document[start : index + 1])

    raise ValueError(f"JSON block not closed for marker: {marker}")


def extract_ytcfg_value(document, key):
    match = re.search(rf'"{re.escape(key)}":"([^"]+)"', document)
    if not match:
        raise ValueError(f"Missing ytcfg key: {key}")
    return match.group(1)


def find_continuation_token(node):
    if isinstance(node, dict):
        continuation = node.get("continuationCommand", {}).get("token")
        if continuation:
            return continuation

        for value in node.values():
            result = find_continuation_token(value)
            if result:
                return result

    if isinstance(node, list):
        for item in node:
            result = find_continuation_token(item)
            if result:
                return result

    return None


def extract_video_renderers(contents):
    videos = []
    continuation = None

    for item in contents:
        if "richItemRenderer" in item:
            content = item["richItemRenderer"].get("content", {})
            video = content.get("videoRenderer")
            if video and video.get("videoId"):
                videos.append(video)

        continuation = continuation or find_continuation_token(item)

    return videos, continuation


def extract_continuation_items(payload):
    items = []

    for action in payload.get("onResponseReceivedActions", []):
        append_items = action.get("appendContinuationItemsAction", {}).get("continuationItems", [])
        if append_items:
            items.extend(append_items)

        reload_items = action.get("reloadContinuationItemsCommand", {}).get("continuationItems", [])
        if reload_items:
            items.extend(reload_items)

    return items


def fetch_stream_page():
    document = fetch_text(SOURCE_URL)
    initial_data = extract_json_assignment(document, "var ytInitialData = ")
    api_key = extract_ytcfg_value(document, "INNERTUBE_API_KEY")
    client_version = extract_ytcfg_value(document, "INNERTUBE_CLIENT_VERSION")
    hl = extract_ytcfg_value(document, "HL")
    gl = extract_ytcfg_value(document, "GL")

    return {
        "document": document,
        "initial_data": initial_data,
        "api_key": api_key,
        "client_version": client_version,
        "hl": hl,
        "gl": gl,
    }


def fetch_more_streams(api_key, client_version, hl, gl, continuation):
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": client_version,
                "hl": hl,
                "gl": gl,
            }
        },
        "continuation": continuation,
    }

    return fetch_json(
        f"https://www.youtube.com/youtubei/v1/browse?key={api_key}",
        payload,
        headers={"Origin": "https://www.youtube.com"},
    )


def derive_label(title, summary):
    lowered = f"{title} {summary}".lower()
    if "dj set" in lowered:
        return "DJ set"
    if "afro" in lowered and "latin" in lowered:
        return "Afro / Latin"
    if "remix" in lowered:
        return "Remix"
    return "Stream"


def derive_status(video):
    badges = video.get("badges", [])
    badge_labels = []
    for badge in badges:
        label = badge.get("metadataBadgeRenderer", {}).get("label")
        if label:
            badge_labels.append(label.lower())

    published_text = text_from_runs(video.get("publishedTimeText")).lower()
    if any("en directo" in label for label in badge_labels):
        return "En directo"
    if published_text.startswith("emitido"):
        return "Emitido"
    if "programad" in published_text:
        return "Programado"
    return "Stream"


def inspect_embed(video_id):
    embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?rel=0"

    try:
        document = fetch_text(embed_url)
    except Exception as exc:
        return {
            "embeddable": False,
            "embed_error": f"No se pudo cargar el embed: {exc}",
        }

    status = extract_first_json_string(document, r'"previewPlayabilityStatus":\{"status":"([^"]+)"')
    reason = extract_first_json_string(document, r'"previewPlayabilityStatus":\{.*?"reason":"([^"]+)"')

    if status == "OK":
        return {"embeddable": True, "embed_error": ""}

    return {
        "embeddable": False,
        "embed_error": reason or "Este stream no se puede reproducir embebido.",
    }


def stream_from_video(video):
    title = text_from_runs(video.get("title")) or f"Stream {video['videoId']}"
    summary = text_from_runs(video.get("descriptionSnippet")) or "Stream de Marques Edition en YouTube."
    video_id = video["videoId"]
    thumbnails = video.get("thumbnail", {}).get("thumbnails", [])
    thumbnail_url = thumbnails[-1]["url"] if thumbnails else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    published_text = text_from_runs(video.get("publishedTimeText"))
    view_count_text = text_from_runs(video.get("viewCountText"))
    duration = text_from_runs(video.get("lengthText"))
    embed_info = inspect_embed(video_id)

    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}",
        "title": shorten(title, 78),
        "summary": shorten(summary, 180),
        "published_text": published_text,
        "view_count_text": view_count_text,
        "duration": duration,
        "label": derive_label(title, summary),
        "status": derive_status(video),
        "thumbnail_url": thumbnail_url,
        "embeddable": embed_info["embeddable"],
        "embed_error": embed_info["embed_error"],
    }


def build_profile(initial_data):
    metadata = initial_data["metadata"]["channelMetadataRenderer"]
    page_header = initial_data["header"]["pageHeaderRenderer"]["content"]["pageHeaderViewModel"]
    metadata_rows = page_header.get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", [])

    handle = CHANNEL_HANDLE
    subscribers = 0
    videos = 0

    for row in metadata_rows:
        for part in row.get("metadataParts", []):
            content = part.get("text", {}).get("content", "")
            lowered = content.lower()
            if content.startswith("@"):
                handle = content
            elif "suscriptor" in lowered:
                subscribers = parse_number(content)
            elif "vídeo" in lowered or "video" in lowered:
                videos = parse_number(content)

    return {
        "handle": handle,
        "title": page_header.get("title", {}).get("dynamicTextViewModel", {}).get("text", {}).get("content", metadata.get("title", "")),
        "channel_id": metadata.get("externalId", ""),
        "channel_url": metadata.get("channelUrl", CHANNEL_URL),
        "source_url": metadata.get("vanityChannelUrl", CHANNEL_URL),
        "subscribers": subscribers,
        "videos": videos,
    }


def build_streams_payload():
    page = fetch_stream_page()
    initial_data = page["initial_data"]
    tabs = initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
    stream_tab = next(tab["tabRenderer"] for tab in tabs if tab.get("tabRenderer", {}).get("selected"))
    grid = stream_tab["content"]["richGridRenderer"]["contents"]

    videos, continuation = extract_video_renderers(grid)

    while continuation:
        continuation_payload = fetch_more_streams(
            page["api_key"],
            page["client_version"],
            page["hl"],
            page["gl"],
            continuation,
        )
        items = extract_continuation_items(continuation_payload)
        if not items:
            break

        next_videos, continuation = extract_video_renderers(items)
        videos.extend(next_videos)

    unique_videos = []
    seen_video_ids = set()
    for video in videos:
        video_id = video.get("videoId")
        if not video_id or video_id in seen_video_ids:
            continue
        seen_video_ids.add(video_id)
        unique_videos.append(video)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_profile": CHANNEL_HANDLE,
        "source_url": STREAMS_URL,
        "profile": build_profile(initial_data),
        "streams": [stream_from_video(video) for video in unique_videos],
    }


def main():
    streams_payload = build_streams_payload()
    payload_json = json.dumps(streams_payload, ensure_ascii=False, indent=2) + "\n"
    OUTPUT_PATH.write_text(payload_json, encoding="utf-8")
    SOURCE_DATA_PATH.write_text(payload_json, encoding="utf-8")

    print(f"Wrote {len(streams_payload['streams'])} streams to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to update streams: {exc}", file=sys.stderr)
        raise
