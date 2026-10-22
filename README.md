# yoyo-app

AI coaching for yoyo tricks: point your camera at yourself, throw, and get told — honestly — what you did right, what you did wrong, and what to practise next. Working name; no logo yet.

- **Feature proposal:** `features.md`
- **Implementation scope, tasks and milestones:** `implementation-plan.md`
- **Current progress and next steps:** `hand-off.md`
- **Defects and known limitations:** `bugtracker.md`
- **Architecture diagram:** `docs/architecture.html`
- **Coaching screen prototype:** `prototype/feedback-screen.html`

## Current state

Nothing is released and no application exists yet. What is real today is the **offline content pipeline** and its output.

- **Repository:** local only. There is no `yoyo-app` repository on GitHub.
- **Pipeline:** working and rerunnable. 16 registered tutorial sources fetch and cache cleanly, repeat runs are idempotent, and the knowledge base passes validation.
- **Knowledge base:** 8 tricks, 45 steps, 29 coach signals, 29 failure modes, all traceable to 15 source videos.
- **Not implemented:** the entire on-device vision stack, the diagnosis and scoring engines, and the app itself. These are designed in `implementation-plan.md` and diagrammed in `docs/architecture.html`; none of it runs.

## The two pipelines

The original idea bundled two very different problems into one. Separating them is the central design decision here.

**① Offline content pipeline** — learn tricks from real tutorials. Search YouTube → pull transcripts → LLM analysis → human curation → trick knowledge base. Cheap, already solved, runs once per trick.

**② On-device real-time pipeline** — watch you throw. Camera → vision stack → signal extraction → trick state machine → diagnosis → score → feedback. Hard, unsolved for yoyo, and the whole reason the product exists.

## Pipeline

```sh
cd yoyo-app

# 1. Fetch transcripts for every registered tutorial.
python pipeline/fetch_transcripts.py            # --force to refetch, --only <trick> to filter

# 2. Inspect and validate the knowledge base.
python pipeline/analyze.py --report             # summary table
python pipeline/analyze.py --validate           # schema + camera-checkability gate
python pipeline/analyze.py --prompt "Trapeze"   # the exact LLM prompt for one trick
```

Dependencies: `youtube-transcript-api` only. Nothing else is required for the content pipeline.

`--validate` is a release gate, not a formality: an entry with no `coach_signals` is rejected, because a trick the camera cannot check is a trick the app cannot coach.

## Boundaries

- This project has **no runtime service, no credentials and no secrets.** Do not add any.
- Video never leaves the device in the intended design; keep it that way. Do not introduce a server-side frame-upload path.
- The knowledge base is grounded in named source videos. Do not add trick content that cannot be traced to a transcript.
- Do not merge the two pipelines. They fail for different reasons and are tracked separately.
