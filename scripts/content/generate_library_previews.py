#!/usr/bin/env python3

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIBRARY_DATA_PATH = ROOT / "src" / "data" / "library.json"
PREVIEW_DIR = ROOT / "public" / "library-previews"
TEMP_DIR = ROOT / ".tmp" / "library-previews"
PREVIEW_SECONDS = 60
PREVIEW_BITRATE = "24k"
PREVIEW_SAMPLE_RATE = "24000"
DEFAULT_WORKERS = 4


def load_library():
    return json.loads(LIBRARY_DATA_PATH.read_text(encoding="utf-8"))


def save_library(payload):
    LIBRARY_DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def iter_tracks(folder):
    for track in folder.get("tracks", []):
        yield track

    for child in folder.get("folders", []):
        yield from iter_tracks(child)


def refresh_preview_flags(folder):
    ready_count = 0

    for track in folder.get("tracks", []):
        preview_path = PREVIEW_DIR / f"{track['id']}.mp3"
        track["preview_url"] = f"/library-previews/{track['id']}.mp3"
        track["preview_ready"] = preview_path.exists()
        if track["preview_ready"]:
            ready_count += 1

    for child in folder.get("folders", []):
        ready_count += refresh_preview_flags(child)

    return ready_count


def build_preview(track, overwrite=False):
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PREVIEW_DIR / f"{track['id']}.mp3"
    temp_path = TEMP_DIR / f"{track['id']}.part.mp3"

    if output_path.exists() and not overwrite:
        return "skipped", track["id"], track["name"], output_path

    if temp_path.exists():
        temp_path.unlink()

    command = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        track["stream_url"],
        "-t",
        str(PREVIEW_SECONDS),
        "-vn",
        "-map_metadata",
        "-1",
        "-ac",
        "1",
        "-ar",
        PREVIEW_SAMPLE_RATE,
        "-b:a",
        PREVIEW_BITRATE,
        "-af",
        "afade=t=in:st=0:d=0.2,afade=t=out:st=57:d=3,lowpass=f=9000",
        str(temp_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        temp_path.replace(output_path)
        return "created", track["id"], track["name"], output_path
    except subprocess.CalledProcessError as exc:
        if temp_path.exists():
            temp_path.unlink()
        return "failed", track["id"], track["name"], exc.stderr.strip()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Genera previews MP3 de 1 minuto para la DJ library."
    )
    parser.add_argument("--limit", type=int, default=0, help="Limita cuántos previews procesar.")
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Número de workers en paralelo. Por defecto: {DEFAULT_WORKERS}.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenera previews ya existentes.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    payload = load_library()
    tracks = list(iter_tracks(payload["library"]))

    if args.limit > 0:
        tracks = tracks[: args.limit]

    print(f"Procesando {len(tracks)} previews con {args.workers} workers...")

    created = 0
    skipped = 0
    failed = []

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {
            executor.submit(build_preview, track, args.overwrite): track for track in tracks
        }

        for index, future in enumerate(as_completed(future_map), start=1):
            status, track_id, track_name, details = future.result()

            if status == "created":
                created += 1
                print(f"[{index}/{len(tracks)}] OK {track_id} {track_name}")
            elif status == "skipped":
                skipped += 1
                print(f"[{index}/{len(tracks)}] SKIP {track_id} {track_name}")
            else:
                failed.append((track_id, track_name, details))
                print(f"[{index}/{len(tracks)}] FAIL {track_id} {track_name}")

    ready_count = refresh_preview_flags(payload["library"])
    payload["stats"]["preview_tracks"] = ready_count
    payload["stats"]["preview_seconds"] = PREVIEW_SECONDS
    save_library(payload)

    print(
        f"Previews listos: {ready_count}. Nuevos: {created}. "
        f"Saltados: {skipped}. Fallidos: {len(failed)}."
    )

    if failed:
        print("\nErrores:")
        for track_id, track_name, details in failed[:20]:
            print(f"- {track_id} | {track_name} | {details}")


if __name__ == "__main__":
    main()
