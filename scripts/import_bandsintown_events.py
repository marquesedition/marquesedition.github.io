#!/usr/bin/env python3

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "src" / "data" / "events.json"


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text or "").strip()


class BandsintownHTMLParser(HTMLParser):
    FIELD_CLASS_MAP = {
        "event-date": "date_label",
        "event-artist": "artist",
        "event-location": "location",
        "event-venue": "venue",
    }

    def __init__(self):
        super().__init__()
        self.events = []
        self.current_month_id = ""
        self.current_month_label = ""
        self.current_event = None
        self.current_event_depth = 0
        self.current_field = None
        self.current_offer = None
        self.current_offer_text = []
        self.capture_month_label = False
        self.month_label_chunks = []

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        classes = set(attr_map.get("class", "").split())

        if tag == "h3" and "event-month-header" in classes:
            self.current_month_id = attr_map.get("id", "")
            self.current_month_label = ""
            self.capture_month_label = True
            self.month_label_chunks = []
            return

        if tag == "div" and "event-item" in classes:
            self.current_event = {
                "month_id": self.current_month_id,
                "month_label": self.current_month_label,
                "date_label": "",
                "artist": "",
                "location": "",
                "venue": "",
                "offers": [],
            }
            self.current_event_depth = 1
            return

        if self.current_event:
            if tag == "div":
                self.current_event_depth += 1
            if tag == "p":
                for class_name, field_name in self.FIELD_CLASS_MAP.items():
                    if class_name in classes:
                        self.current_field = field_name
                        return
            if tag == "a" and "event-ticket-link" in classes:
                self.current_offer = {"label": "", "url": attr_map.get("href", "")}
                self.current_offer_text = []

    def handle_endtag(self, tag):
        if tag == "h3" and self.capture_month_label:
            raw_label = normalize_whitespace("".join(self.month_label_chunks))
            self.current_month_label = re.sub(r"\(\d+\)$", "", raw_label).strip()
            self.capture_month_label = False
            self.month_label_chunks = []
            return

        if self.current_event:
            if tag == "p" and self.current_field:
                self.current_field = None
                return
            if tag == "a" and self.current_offer:
                self.current_offer["label"] = normalize_whitespace("".join(self.current_offer_text))
                self.current_event["offers"].append(self.current_offer)
                self.current_offer = None
                self.current_offer_text = []
                return
            if tag == "div":
                self.current_event_depth -= 1
                if self.current_event_depth == 0:
                    self.events.append(
                        {
                            **self.current_event,
                            "date_label": normalize_whitespace(self.current_event["date_label"]),
                            "artist": normalize_whitespace(self.current_event["artist"]),
                            "location": normalize_whitespace(self.current_event["location"]),
                            "venue": normalize_whitespace(self.current_event["venue"]),
                            "offers": [
                                offer
                                for offer in self.current_event["offers"]
                                if offer["label"] and offer["url"]
                            ],
                        }
                    )
                    self.current_event = None

    def handle_data(self, data):
        if self.capture_month_label:
            self.month_label_chunks.append(data)
        if self.current_event and self.current_field:
            self.current_event[self.current_field] += data
        if self.current_offer is not None:
            self.current_offer_text.append(data)


def read_input(path):
    if path:
        return Path(path).read_text(encoding="utf-8")

    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise SystemExit(
        "Provide a Bandsintown HTML file path or pipe the HTML snippet via stdin."
    )


def build_payload(html_text, artist_override=None, source_url=""):
    parser = BandsintownHTMLParser()
    parser.feed(html_text)

    artist = artist_override or ""
    if not artist:
        for event in parser.events:
            if event["artist"]:
                artist = event["artist"]
                break

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "bandsintown_html",
        "source_url": source_url,
        "artist": artist or "Marques Edition",
        "events": parser.events,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Import a Bandsintown HTML block into src/data/events.json"
    )
    parser.add_argument("input", nargs="?", help="Path to an HTML file with .bandsintown-events")
    parser.add_argument("--artist", help="Override artist name in output")
    parser.add_argument("--source-url", default="", help="Reference URL for the imported source")
    args = parser.parse_args()

    html_text = read_input(args.input)
    payload = build_payload(html_text, artist_override=args.artist, source_url=args.source_url)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(payload['events'])} events to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
