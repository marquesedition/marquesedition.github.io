#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "src" / "data" / "events.json"
TIMEZONE = ZoneInfo("Europe/Madrid")

RESIDENCY = {
    "title": "Residencia fija en Pensión Mimosas",
    "venue": "Pensión Mimosas",
    "address": "C. del Marqués Viudo de Pontejos, 9, 28012 Madrid",
    "location": "Madrid, España",
    "area": "Sol / Centro",
    "days_of_week": [4, 5],  # Friday, Saturday
    "start_time": "21:00",
    "end_time": "02:30",
    "map_url": "https://share.google/YZcMnADktdv1w7FEW",
    "venue_url": "https://www.esmadrid.com/en/nightlife/pension-mimosas",
    "artist": "Marques Edition",
    "count": 20,
}

DAY_NAMES = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]


def format_month_label(date_value):
    months = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    return f"{months[date_value.month - 1].capitalize()} de {date_value.year}"


def format_date_label(date_value):
    day_name = DAY_NAMES[date_value.weekday()]
    months = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    return f"{day_name.capitalize()} {date_value.day} de {months[date_value.month - 1]} de {date_value.year}"


def generate_residency_events():
    now = datetime.now(TIMEZONE).date()
    current = now
    events = []

    while len(events) < RESIDENCY["count"]:
      if current.weekday() in RESIDENCY["days_of_week"]:
        events.append(
            {
                "month_id": current.strftime("%Y-%m"),
                "month_label": format_month_label(current),
                "date_label": format_date_label(current),
                "artist": RESIDENCY["artist"],
                "location": f"{RESIDENCY['area']}, {RESIDENCY['location']}",
                "venue": f"{RESIDENCY['venue']} · {RESIDENCY['start_time']} - {RESIDENCY['end_time']}",
                "offers": [
                    {"label": "Cómo llegar", "url": RESIDENCY["map_url"]},
                    {"label": "Ver local", "url": RESIDENCY["venue_url"]},
                ],
            }
        )
      current += timedelta(days=1)

    return events


def build_payload():
    return {
        "generated_at": datetime.now(TIMEZONE).isoformat(),
        "source": "recurring_residency",
        "source_url": RESIDENCY["map_url"],
        "artist": RESIDENCY["artist"],
        "featured_residency": {
            "title": RESIDENCY["title"],
            "venue": RESIDENCY["venue"],
            "location": RESIDENCY["location"],
            "area": RESIDENCY["area"],
            "address": RESIDENCY["address"],
            "schedule_label": "Todos los viernes y sábados",
            "time_label": f"{RESIDENCY['start_time']} - {RESIDENCY['end_time']}",
            "map_url": RESIDENCY["map_url"],
            "venue_url": RESIDENCY["venue_url"],
        },
        "events": generate_residency_events(),
    }


def main():
    payload = build_payload()
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    OUTPUT_PATH.write_text(payload_json, encoding="utf-8")
    print(f"Wrote {len(payload['events'])} events to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
