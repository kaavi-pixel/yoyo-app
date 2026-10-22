#!/usr/bin/env python
"""
yoyo-app :: step 2 of the knowledge pipeline
============================================
Turn raw tutorial transcripts into the structured trick knowledge base.

The original idea said: "analyse how the trick works, then [take the] advice
they give on making it easier."

That is exactly this step. It is an LLM task, so this script has two jobs:

  1. Hold the PROMPT + SCHEMA that make the analysis reproducible and
     re-runnable as new tutorials arrive (--prompt prints the exact prompt
     to send the model for a given trick).
  2. VALIDATE the resulting knowledge base so a hallucinated or incomplete
     entry can never reach the coaching layer (--validate).

The critical field is `coach_signals`. It is the contract between the
transcript pipeline (what humans teach) and the camera pipeline (what the
vision model can actually observe). A trick entry with no coach_signals is
useless to the app, so validation treats it as an error.

Usage:
    python analyze.py --validate                 # check the KB
    python analyze.py --prompt "Trapeze"         # print the analysis prompt
    python analyze.py --report                   # human-readable KB summary
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "knowledge_base" / "tricks.json"
TRANSCRIPTS = ROOT / "data" / "transcripts"

REQUIRED_TRICK_FIELDS = ["trick", "style", "level", "difficulty_1_9", "definition", "steps", "coach_signals", "source_videos"]
REQUIRED_STEP_FIELDS = ["n", "do"]
VALID_STYLES = {"1A", "2A", "3A", "4A", "5A"}
VALID_LEVELS = {"beginner", "intermediate", "advanced"}

PROMPT_TEMPLATE = """\
You are building the knowledge base for a yoyo-coaching app. You will be given
the transcripts of several real tutorials for ONE yoyo trick, plus metadata.

Extract a single structured trick entry. Rules:

1. GROUND EVERYTHING. Every step, cue and failure mode must be traceable to the
   transcripts. Do not add generic yoyo advice that was not taught in a source.
2. SEPARATE TEACHING FROM OBSERVATION. `steps`, `key_cues`, `failure_modes`
   come from what instructors say. `coach_signals` is different: it is what a
   CAMERA could measure. Translate teaching into physics. "Keep your palm up" is
   a cue; "hand vertical travel in the first 300ms after release" is a signal.
3. FAILURE MODES MUST BE DIAGNOSTIC, not just "it didn't work". Each entry
   needs: symptom (what the player SEES), cause (the mechanical reason), fix
   (the spoken instruction). Prefer instructors' own diagnoses.
4. DIFFICULTY is 1-9 on the community trick-ladder scale (1 = first sleeper,
   9 = contest-level).
5. BE HONEST in the score rubric. The app must not be sycophantic - a 10 means
   genuinely clean and consistent, not "nice try".
6. If a field cannot be grounded in the transcripts, use null or an empty list.
   NEVER invent a step to fill space.

Return ONLY JSON matching this schema:

{schema}

TRICK: {trick}
SOURCE METADATA: {meta}

TRANSCRIPTS:
{transcripts}
"""


def load_kb() -> dict:
    if not KB.exists():
        sys.exit(f"No knowledge base at {KB}. Run the analysis step first.")
    return json.loads(KB.read_text(encoding="utf-8"))


def validate(kb: dict) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for i, t in enumerate(kb.get("tricks", [])):
        where = f"tricks[{i}] ({t.get('trick', '?')})"
        for field in REQUIRED_TRICK_FIELDS:
            if field not in t:
                errors.append(f"{where}: missing required field '{field}'")
        name = t.get("trick")
        if name in seen:
            errors.append(f"{where}: duplicate trick name")
        seen.add(name)

        if t.get("style") not in VALID_STYLES:
            errors.append(f"{where}: bad style {t.get('style')!r} (expected one of {sorted(VALID_STYLES)})")
        if t.get("level") not in VALID_LEVELS:
            errors.append(f"{where}: bad level {t.get('level')!r}")

        d = t.get("difficulty_1_9")
        if not isinstance(d, (int, float)) or not (1 <= d <= 9):
            errors.append(f"{where}: difficulty_1_9 must be a number 1-9, got {d!r}")

        steps = t.get("steps") or []
        if not steps:
            errors.append(f"{where}: no steps - useless to the coach")
        for j, s in enumerate(steps):
            missing = [f for f in REQUIRED_STEP_FIELDS if f not in s]
            if missing:
                errors.append(f"{where}.steps[{j}]: missing {missing}")
        if steps and [s.get("n") for s in steps] != list(range(1, len(steps) + 1)):
            errors.append(f"{where}: step numbers are not 1..{len(steps)}")

        # The important one: a trick the camera cannot check cannot be coached.
        signals = t.get("coach_signals") or []
        if not signals:
            errors.append(f"{where}: no coach_signals - the vision layer has nothing to check")
        for j, s in enumerate(signals):
            if not s.get("signal") or not s.get("good"):
                errors.append(f"{where}.coach_signals[{j}]: needs both 'signal' and 'good'")

        for j, fm in enumerate(t.get("failure_modes") or []):
            missing = [f for f in ("symptom", "cause", "fix") if not fm.get(f)]
            if missing:
                errors.append(f"{where}.failure_modes[{j}]: incomplete diagnosis, missing {missing}")

        srcs = t.get("source_videos") or []
        if not srcs:
            errors.append(f"{where}: no source_videos - not traceable")
        for s in srcs:
            vid = s.get("video_id", "")
            if len(vid) != 11 or not all(c.isalnum() or c in "-_" for c in vid):
                errors.append(f"{where}: bad video_id {vid!r}")
            elif not (TRANSCRIPTS / f"{vid}.txt").exists():
                errors.append(f"{where}: video_id {vid} has no cached transcript on disk")

    return errors


def build_prompt(trick: str) -> str:
    """Assemble the real analysis prompt for one trick from cached transcripts."""
    kb_schema = json.loads(KB.read_text(encoding="utf-8"))["schema"] if KB.exists() else {}
    registry = json.loads((ROOT / "pipeline" / "sources.json").read_text(encoding="utf-8"))
    srcs = [s for s in registry["sources"] if trick.lower() in s["trick"].lower()]
    if not srcs:
        return f"No sources registered for trick matching {trick!r}."

    chunks = []
    for s in srcs:
        p = TRANSCRIPTS / f"{s['video_id']}.txt"
        if p.exists():
            chunks.append(f"--- {s['channel']} | {s['title']} ({s['video_id']}) ---\n{p.read_text(encoding='utf-8')}")

    meta = [{k: s[k] for k in ("channel", "title", "video_id", "level", "style")} for s in srcs]
    return PROMPT_TEMPLATE.format(
        schema=json.dumps(kb_schema, indent=2, ensure_ascii=False),
        trick=srcs[0]["trick"],
        meta=json.dumps(meta, indent=2),
        transcripts="\n\n".join(chunks),
    )


def report(kb: dict) -> None:
    tricks = kb["tricks"]
    print(f"Knowledge base v{kb.get('version')} - {len(tricks)} tricks\n")
    print(f"{'TRICK':<28} {'STYLE':<6} {'LEVEL':<13} {'DIFF':<5} {'STEPS':<6} {'SIGNALS':<8} {'FAILS':<6} SRC")
    print("-" * 92)
    for t in tricks:
        print(f"{t['trick'][:27]:<28} {t['style']:<6} {t['level']:<13} "
              f"{t['difficulty_1_9']:<5} {len(t.get('steps', [])):<6} "
              f"{len(t.get('coach_signals', [])):<8} {len(t.get('failure_modes', [])):<6} "
              f"{len(t.get('source_videos', []))}")
    total_steps = sum(len(t.get("steps", [])) for t in tricks)
    total_sig = sum(len(t.get("coach_signals", [])) for t in tricks)
    total_fail = sum(len(t.get("failure_modes", [])) for t in tricks)
    total_src = sum(len(t.get("source_videos", [])) for t in tricks)
    print("-" * 92)
    print(f"{'TOTAL':<28} {'':<6} {'':<13} {'':<5} {total_steps:<6} {total_sig:<8} {total_fail:<6} {total_src}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--prompt", metavar="TRICK")
    args = ap.parse_args()

    if args.prompt:
        print(build_prompt(args.prompt))
        return 0

    kb = load_kb()
    if args.report or not args.validate:
        report(kb)
    if args.validate:
        errors = validate(kb)
        print()
        if errors:
            print(f"FAILED - {len(errors)} problem(s):")
            for e in errors:
                print(f"  - {e}")
            return 1
        print("PASS - knowledge base is valid and fully camera-checkable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
