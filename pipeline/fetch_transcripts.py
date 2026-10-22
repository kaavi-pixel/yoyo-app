#!/usr/bin/env python
"""
yoyo-app :: step 1 of the knowledge pipeline
============================================
Fetch transcripts for every tutorial in sources.json and cache them to disk.

This is the "Search youtube for 'x yoyo tutorial' and find good quality videos
and their transcripts. Put them in a folder" part of the original idea, made
real and repeatable.

Usage:
    python fetch_transcripts.py                 # fetch everything missing
    python fetch_transcripts.py --force         # refetch everything
    python fetch_transcripts.py --only Trapeze  # one trick

Output:
    data/transcripts/<video_id>.json   full transcript w/ timestamps + metadata
    data/transcripts/<video_id>.txt    plain narration text (what the analyst reads)
    data/transcripts/manifest.json     index: what succeeded, what failed, when
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "pipeline" / "sources.json"
OUT = ROOT / "data" / "transcripts"

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    sys.exit("Missing dependency: pip install youtube-transcript-api")


def fetch_one(video_id: str, languages=("en", "en-US", "en-GB")) -> dict:
    """Return {'segments': [...], 'language': str} or raise."""
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=list(languages))
    segments = [
        {"start": round(s.start, 2), "dur": round(s.duration, 2), "text": s.text.strip()}
        for s in fetched
    ]
    return {"segments": segments, "language": fetched.language_code}


def clean(text: str) -> str:
    """Strip caption noise so the analyser reads instruction, not scaffolding."""
    text = re.sub(r"\[(music|applause|laughter|silence)\]", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="refetch even if cached")
    ap.add_argument("--only", default=None, help="substring filter on trick name")
    ap.add_argument("--sleep", type=float, default=1.5, help="seconds between requests")
    args = ap.parse_args()

    registry = json.loads(SOURCES.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"entries": []}

    todo = [s for s in registry["sources"] if not args.only or args.only.lower() in s["trick"].lower()]
    # Count what is actually cached on disk, not what the manifest claims.
    already_cached = sum(1 for s in todo if (OUT / f"{s['video_id']}.json").exists())
    print(f"{len(todo)} source(s) selected, {already_cached} already cached")

    results = []
    for i, src in enumerate(todo, 1):
        vid = src["video_id"]
        json_path = OUT / f"{vid}.json"
        txt_path = OUT / f"{vid}.txt"

        if json_path.exists() and not args.force:
            print(f"  [{i}/{len(todo)}] {vid}  cached, skipping")
            cached = json.loads(json_path.read_text(encoding="utf-8"))
            results.append({
                "video_id": vid, "status": "ok",
                "trick": src["trick"], "channel": src["channel"], "title": src["title"],
                "level": src["level"], "style": src["style"], "url": cached.get("url"),
                "language": cached.get("language"), "segment_count": cached.get("segment_count"),
                "chars": len(txt_path.read_text(encoding="utf-8")) if txt_path.exists() else None,
                "fetched_at": cached.get("fetched_at"),
            })
            continue

        print(f"  [{i}/{len(todo)}] {vid}  {src['trick']} :: {src['channel']} ...", end="", flush=True)
        try:
            data = fetch_one(vid)
            segments = data["segments"]
            payload = {
                "video_id": vid,
                "trick": src["trick"],
                "level": src["level"],
                "style": src["style"],
                "channel": src["channel"],
                "title": src["title"],
                "url": f"https://www.youtube.com/watch?v={vid}",
                "language": data["language"],
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "segment_count": len(segments),
                "segments": segments,
            }
            json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

            narration = clean(" ".join(s["text"] for s in segments))
            txt_path.write_text(narration, encoding="utf-8")

            print(f" ok ({len(segments)} segments, {len(narration)} chars)")
            results.append({
                "video_id": vid, "status": "ok", "trick": src["trick"], "channel": src["channel"],
                "title": src["title"], "level": src["level"], "style": src["style"],
                "url": payload["url"], "language": data["language"],
                "segment_count": len(segments), "chars": len(narration),
                "fetched_at": payload["fetched_at"],
            })
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f" FAILED: {type(exc).__name__}: {str(exc)[:120]}")
            results.append({"video_id": vid, "status": "failed", "error": f"{type(exc).__name__}: {exc}",
                            "trick": src["trick"], "channel": src["channel"]})

        time.sleep(args.sleep)

    # merge (newest wins per video_id)
    by_id = {e["video_id"]: e for e in manifest["entries"]}
    for r in results:
        by_id[r["video_id"]] = r
    manifest["entries"] = sorted(by_id.values(), key=lambda e: (e.get("trick", ""), e["video_id"]))
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["counts"] = {
        "ok": sum(1 for e in manifest["entries"] if e.get("status") == "ok"),
        "failed": sum(1 for e in manifest["entries"] if e.get("status") == "failed"),
        "sources_registered": len(registry["sources"]),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nmanifest: {manifest['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
