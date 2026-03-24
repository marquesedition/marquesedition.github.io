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
HOME_PATH = Path("index.html")
MEDIA_LINKS_PATH = Path("media-links/index.html")


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
        return "Instagram reel de Marques Edition."

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
    return "Instagram reel"


def reel_from_node(node):
    caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
    caption = ""
    if caption_edges:
        caption = caption_edges[0].get("node", {}).get("text", "").strip()

    lines = [line.strip() for line in caption.splitlines() if line.strip()]
    shortcode = node["shortcode"]
    timestamp = node["taken_at_timestamp"]
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()

    return {
        "shortcode": shortcode,
        "url": f"https://www.instagram.com/reel/{shortcode}/",
        "date": date,
        "timestamp": timestamp,
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


def format_display_date(date_value):
    months = [
        "ene",
        "feb",
        "mar",
        "abr",
        "may",
        "jun",
        "jul",
        "ago",
        "sep",
        "oct",
        "nov",
        "dic",
    ]
    dt = datetime.fromisoformat(date_value)
    return f"{dt.day:02d} {months[dt.month - 1]} {dt.year}"


def format_profile_number(value):
    return f"{value:,}".replace(",", ".")


def format_compact_number(value):
    if value >= 1000:
        whole = value / 1000
        if whole.is_integer():
            return f"{int(whole)}k"
        return f"{whole:.1f}".replace(".", ",") + "k"
    return str(value)


def replace_generated_block(text, marker_name, content):
    pattern = re.compile(
        rf"(<!-- GENERATED:{marker_name}_START -->)(.*?)(<!-- GENERATED:{marker_name}_END -->)",
        re.S,
    )
    replacement = f"\\1\n{content.rstrip()}\n\\3"
    updated, count = pattern.subn(replacement, text)
    if count != 1:
        raise ValueError(f"Marker {marker_name} not found exactly once")
    return updated


def render_home_stats(profile, reels):
    items = [
        (format_compact_number(profile["followers"]), "Seguidores"),
        (str(len(reels)), "Reels"),
        (str(profile["posts"]), "Posts"),
        (str(profile["highlights"]), "Highlights"),
    ]
    return "\n".join(
        [
            "              <div class=\"stat\">"
            f"\n                <strong>{html.escape(value)}</strong>"
            f"\n                <span>{html.escape(label)}</span>"
            "\n              </div>"
            for value, label in items
        ]
    )


def render_home_latest(reel):
    return (
        f"              <p class=\"latest-title\">{html.escape(reel['title'])}</p>\n"
        f"              <p class=\"latest-meta\">{html.escape(format_display_date(reel['date']))} · {html.escape(reel['label'])}</p>"
    )


def render_media_proof(profile, reels):
    items = [
        (format_compact_number(profile["followers"]), "Seguidores"),
        (str(len(reels)), "Reels públicos"),
        (str(profile["posts"]), "Posts"),
        (str(profile["highlights"]), "Highlights"),
    ]
    return "\n".join(
        [
            "                <div class=\"proof-card\">"
            f"\n                  <strong>{html.escape(value)}</strong>"
            f"\n                  <span>{html.escape(label)}</span>"
            "\n                </div>"
            for value, label in items
        ]
    )


def render_reel_card(reel, index, is_hero=False):
    card_class = "reel-card reel-card--hero" if is_hero else "reel-card"
    rank_class = "reel-rank reel-rank--hero" if is_hero else "reel-rank"
    flag = "Último reel" if is_hero else "Reel"
    url = html.escape(reel["url"])
    title = html.escape(reel["title"])
    meta = html.escape(format_display_date(reel["date"]))
    summary = html.escape(reel["summary"])
    label = html.escape(reel["label"])

    return f"""              <article class="{card_class}">
                <div class="reel-topline">
                  <span class="{rank_class}">#{index}</span>
                  <span class="reel-flag">{html.escape(flag)}</span>
                </div>
                <h3>{title}</h3>
                <p class="reel-meta">{meta}</p>
                <p class="reel-desc">{summary}</p>
                <div class="reel-embed">
                  <blockquote
                    class="instagram-media"
                    data-instgrm-permalink="{url}"
                    data-instgrm-version="14"
                    style="background:#120b31; border:0; margin:0; padding:0; width:100%;"
                  >
                    <a href="{url}" target="_blank" rel="noopener noreferrer">Ver reel en Instagram</a>
                  </blockquote>
                </div>
                <div class="reel-footer">
                  <span class="reel-label">{label}</span>
                  <a class="reel-link" href="{url}" target="_blank" rel="noopener noreferrer">Abrir reel ↗</a>
                </div>
              </article>"""


def render_featured_reels(reels):
    return "\n\n".join(
        render_reel_card(reel, index + 1, is_hero=index == 0)
        for index, reel in enumerate(reels[:4])
    )


def render_all_reels(reels):
    return "\n\n".join(
        render_reel_card(reel, index + 5, is_hero=False)
        for index, reel in enumerate(reels[4:])
    )


def render_reels_generated(payload):
    date = format_display_date(payload["generated_at"][:10])
    return (
        f"{len(payload['reels'])} reels · actualizado {html.escape(date)} · "
        f"<a href=\"{html.escape(payload['source_url'])}\" target=\"_blank\" rel=\"noopener noreferrer\">abrir perfil ↗</a>"
    )


def update_home_html(reels_payload):
    text = HOME_PATH.read_text(encoding="utf-8")
    text = replace_generated_block(
        text,
        "HOME_STATS",
        render_home_stats(reels_payload["profile"], reels_payload["reels"]),
    )
    text = replace_generated_block(
        text,
        "HOME_LATEST",
        render_home_latest(reels_payload["reels"][0]),
    )
    HOME_PATH.write_text(text, encoding="utf-8")


def update_media_links_html(reels_payload):
    reels = reels_payload["reels"]
    profile = reels_payload["profile"]
    text = MEDIA_LINKS_PATH.read_text(encoding="utf-8")
    text = replace_generated_block(
        text,
        "INSTAGRAM_LINK_META",
        f"{format_profile_number(profile['followers'])} seguidores",
    )
    text = replace_generated_block(
        text,
        "MEDIA_PROOF",
        render_media_proof(profile, reels),
    )
    text = replace_generated_block(
        text,
        "FEATURED_REELS",
        render_featured_reels(reels),
    )
    text = replace_generated_block(
        text,
        "ALL_REELS_SUMMARY",
        f"Ver todos los reels ({len(reels)})",
    )
    text = replace_generated_block(
        text,
        "ALL_REELS",
        render_all_reels(reels),
    )
    text = replace_generated_block(
        text,
        "REELS_META",
        render_reels_generated(reels_payload),
    )
    MEDIA_LINKS_PATH.write_text(text, encoding="utf-8")


def main():
    payload = fetch_profile_payload()
    reels_payload = build_reels_payload(payload)

    OUTPUT_PATH.write_text(
        json.dumps(reels_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    update_home_html(reels_payload)
    update_media_links_html(reels_payload)

    print(f"Wrote {len(reels_payload['reels'])} reels to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to update reels: {exc}", file=sys.stderr)
        raise
