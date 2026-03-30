#!/usr/bin/env python3

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TARGETS = [
    "index.html",
    "about",
    "booking",
    "events",
    "media-links",
    "reels",
    "reel-thumbs",
    "sets",
    "sessions",
    "streams",
    "audio",
    "_astro",
    "logo.png",
    "profile.png",
    "favicon.ico",
    "favicon.svg",
    "favicon-48x48.png",
    "apple-touch-icon.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "site.webmanifest",
    "CNAME",
    "404.html",
    "robots.txt",
    "sitemap.xml",
]


def remove_target(path: Path):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def copy_target(source: Path, target: Path):
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def write_text_file(path: Path, content: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main():
    if not DIST.exists():
        raise SystemExit("dist directory not found. Run the Astro build first.")

    for name in TARGETS:
        target = ROOT / name
        source = DIST / name
        remove_target(target)
        if source.exists():
            copy_target(source, target)

    # GitHub Pages ignores paths starting with "_" unless .nojekyll is present.
    write_text_file(DIST / ".nojekyll")
    write_text_file(ROOT / ".nojekyll")


if __name__ == "__main__":
    main()
