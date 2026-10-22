# yoyo-app Implementation Plan

Status: M1 (content pipeline) implemented and validated locally. M2 (vision stack) not started and is the critical unknown. Nothing is released; no application exists yet. Updated: 2026-10-22.

This plan defines the intended behaviour and delivery sequence for an app that watches you throw a yoyo and coaches you. It does not claim that any camera functionality has been built or tested. The offline content pipeline is built and its output is real; the on-device pipeline is design only.

## Problem and goals

Yoyo is a *state* sport, not a *pose* sport. A squat is right or wrong against a fixed joint angle; a trapeze is right when the string lands on the right finger in the right segment, and there are several valid ways to reach that state. This distinction drives every decision below.

- **Honest coaching:** Report execution, not effort. A low score with a specific, actionable cause is more useful than encouragement.
- **Diagnosis over verdict:** "You missed on the outside of the string because your yoyo hand was too close to your body" beats "8/10, nice throw".
- **Grounding:** Every piece of advice must trace to a real tutorial transcript. The app must not invent yoyo instruction.
- **Privacy by architecture:** Video never leaves the device. No frame upload, no per-frame cloud cost, no account required for v1.
- **Tractable v1:** Ask "did the trick land, and if not, at which step did it fail?" before attempting "rate my form 1–10".

Acceptance is measured by the verification scenarios below, not by feature count. A trick the camera cannot check is not a supported trick; it is content.

## Scope and boundaries

### Core release (v1)

- **Style:** 1A string tricks only. One yoyo, one hand, vertical plane.
- **Trick set:** The 8 tricks already in the knowledge base, led by Trapeze, Sleeper, Bind and Brain Scrambler.
- **Capture:** One camera angle, phone rear camera, 60 fps minimum.
- **Vision:** Hand landmarks plus a custom yoyo/string detector. The custom detector is the deliverable that makes the product possible.
- **Coaching:** Landed / not landed, failure point located to a numbered step, one diagnosis with cause and fix, honest 0–10 score against the trick rubric.
- **Platform:** iOS and Android, on-device inference, local-first storage.

### Staged follow-up

- **Progress tracking:** Streaks, per-trick attempt history, and the 1–9 trick ladder as a progression view. Add once a single trick coaches reliably.
- **Video review:** Step-by-step replay of a failed attempt with the failure frame marked.
- **Additional styles:** 2A, 3A, 4A and 5A. Much harder to observe — two yoyos, or a yoyo detached from the string — and each needs its own detector work.
- **Other skill toys:** Juggling, kendama, diabolo, footbag, spin top. The pipeline generalises; the vision work does not.
- **Multiple angles:** A second camera or angle for depth-sensitive diagnosis.

Out of scope: real-time frame-by-frame pose critique at contest level, automatic freestyle judging, social or competitive features, hardware sensors, cloud video storage.

## User stories

- **Beginner:** As someone who just bought a yoyo, I want to know whether I am even doing the throw right, so that I do not build a bad habit I have to unlearn.
- **Practising player:** As someone stuck on a trick, I want to be told the specific step that keeps failing, so that I can practise the right thing instead of repeating the whole trick.
- **Solitary player:** As someone with no club nearby, I want feedback that does not depend on another person watching and judging me.
- **Honest-feedback seeker:** As a player who is improving, I want a score that reflects my execution so that I can tell real progress from feeling good about a bad attempt.
- **Privacy-conscious player:** As someone filming myself at home, I want the app to work without uploading video of my room, my hands or my face.
- **Operator:** As the maintainer, I want trick content grounded in named sources so that the app cannot confidently teach something no instructor ever said.

## Task list

Prefix `YA-`. Checkboxes reflect actual local state, verified by running the pipeline.

### M0: Discovery and feasibility

- [x] YA-00A Establish whether sufficient tutorial content exists. Result: yes, in excess — 429 trick videos on YoYoTricks alone, 1000+ in the REWIND database, 1000+ tutorials on Skill Addicts, with transcripts available.
- [x] YA-00B Establish whether comparable coaching products exist. Result: none do real-time AI camera coaching for yoyo. Skill Addicts does community-review-based feedback for 20k+ learners; YoYoTricks' "Level Up!" is a structured video library; ThrowLog is a tracker.
- [x] YA-00C Establish whether the vision problem is solved off the shelf. Result: partially. Body and hand pose estimation is commodity (MediaPipe Hands 21 landmarks, Pose 33 landmarks). Detecting the yoyo and the string path is custom. A 2023 skateboard trick-classification study with YOLO+CNN/RNN reached only 36% accuracy on 439 labelled tricks and did not confirm feasibility.
- [x] YA-00D Establish market size and positioning. Result: yoyo alone is niche (~9k–30k serious throwers worldwide; ~USD 405M toy market, ~5% CAGR). Position as skill-toy coaching with yoyo as the beachhead.
- [ ] YA-00E Confirm the v1 trick and camera angle with Kavi before any detector work begins.

### M1: Offline content pipeline

- [x] YA-10A Curated source registry. `pipeline/sources.json`, 16 sources across 8 tricks, quality-filtered for verbal instruction rather than music-only demos.
- [x] YA-10B Transcript fetcher with caching and manifest. `pipeline/fetch_transcripts.py`. 16/16 fetched, 0 failures, repeat runs idempotent.
- [x] YA-10C Analysis prompt, schema and validator. `pipeline/analyze.py`, including the `coach_signals` release gate.
- [x] YA-10D Trick knowledge base v0.1.0. `data/knowledge_base/tricks.json` — 8 tricks, 45 steps, 29 coach signals, 29 failure modes, 15 source references.
- [ ] YA-10E Widen the trick set. Target the full 1A beginner ladder plus 10–20 intermediate tricks.
- [ ] YA-10F Automate the human curation gate so an ungrounded entry cannot be committed.
- [ ] YA-10G Normalise garbled auto-caption terms before analysis (see YO-002).

### M2: Vision stack (critical path)

- [ ] YA-20A Capture harness at 60 fps with a timestamped ring buffer covering one full attempt.
- [ ] YA-20B Hand landmark tracking using an off-the-shelf model; validate both hands under real throw lighting.
- [ ] YA-20C Yoyo detector. Train on footage filmed for this purpose. This is the highest-risk item in the plan.
- [ ] YA-20D String path estimation. Requires the yoyo detector and hand landmarks to be stable first.
- [ ] YA-20E Signal extraction layer producing the quantities named in `coach_signals` — spin duration, spin plane, hand travel, hop events, string configuration transitions.
- [ ] YA-20F Benchmark on mid-range hardware. Must hold the latency budget with no frame leaving the device.

### M3: Coach layer

- [ ] YA-30A Trick state machine driven by the knowledge base's `coach_signals`.
- [ ] YA-30B Failure-point locator. Maps a failed attempt to the numbered step where the state diverged.
- [ ] YA-30C Diagnosis engine using the `failure_modes` tables (symptom → cause → fix).
- [ ] YA-30D Score engine against the per-trick `score_rubric`. Must be able to return a low score.

### M4: Application and experience

- [ ] YA-40A Camera capture screen with skeleton and string overlay.
- [ ] YA-40B Post-attempt coaching report: rating, what you did right, what went wrong, next drill.
- [ ] YA-40C Local attempt and progress storage; this doubles as the training corpus.
- [ ] YA-40D Trick browser with prerequisites and the 1–9 difficulty ladder.

### M5: Hardening and release

- [ ] YA-50A Confirm no network path can carry frames or clips.
- [ ] YA-50B Battery and thermal testing across a 20-minute practice session.
- [ ] YA-50C Accessibility: colour-blind-safe overlays, captions, adjustable feedback pace.
- [ ] YA-50D Store submission, privacy disclosure, and a closed pilot with real yoyo players.

### M6: Expansion

- [ ] YA-60A 2A looping. Two yoyos, continuous motion — needs new detector work.
- [ ] YA-60B 3A two-handed string tricks.
- [ ] YA-60C 4A offstring. Detached yoyo; the hardest observation problem of the five styles.
- [ ] YA-60D 5A counterweight.
- [ ] YA-60E Evaluate the same pipeline for juggling or kendama.

## Milestones

| Milestone | Exit gate |
|---|---|
| M0: Discovery and feasibility | Kavi confirms the v1 trick and camera angle |
| M1: Content pipeline | Knowledge base validated and widened; curation gate automated |
| M2: Vision stack | Trapeze landed/not-landed detection at a usable rate on mid-range hardware, on-device |
| M3: Coach layer | A failed Trapeze is mapped to the correct step, with the correct diagnosis, in a held-out test set |
| M4: Application | A player with no supervision completes a full learn-and-practise loop |
| M5: Hardening and release | Closed pilot with real players; no network path for video |
| M6: Expansion | A second style (2A) coaches at the same quality as 1A |

## Verification scenarios

1. **Landed, clean.** A recorded Trapeze that lands with correct alignment scores in the upper band and names no fault.
2. **Outside miss.** A recording of the specific outside-miss fault is diagnosed as yoyo hand too close to the body, and the fix shown matches the source tutorial's own diagnosis.
3. **Inside miss.** The mirror fault is diagnosed as the hand too far from the body, not confused with scenario 2.
4. **No false confidence.** An attempt where the camera loses the yoyo mid-flight must return "could not track this attempt", never a score.
5. **Honest low score.** A beginner attempt that fails every time scores in the lowest band and says so.
6. **Privacy.** With the device's network interface disabled, the full capture-to-feedback loop still completes.
7. **Content gate.** Adding a trick entry with an empty `coach_signals` list fails `pipeline/analyze.py --validate`.
8. **Traceability.** Every statement shown to a player resolves to a `source_videos` entry on the trick it came from.
