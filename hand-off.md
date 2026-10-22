# yoyo-app Hand-off

Updated: 2026-10-22. Current work: offline content pipeline delivered and validated; vision stack not started.

This is the live progress record. Scope, task definitions and acceptance scenarios live in `implementation-plan.md`; this document records what has actually been done and what the next implementer should do.

## Current state

- **Repository:** local only, at `C:\Users\kavsb\projects\yoyo-app`. **There is no `yoyo-app` repository on GitHub.** None of the nine repositories under `kaavi-pixel` is this project, and no remote is configured. Publication is an open decision, not a completed step.
- **Released:** nothing. There is no application, no build, no store presence and no closed pilot.
- **Content pipeline:** implemented and rerunnable. `pipeline/fetch_transcripts.py` retrieved 16 of 16 registered sources with zero failures. Repeat runs are idempotent — the manifest holds at `ok: 16` across consecutive runs (defect YO-001 fixed, see `bugtracker.md`).
- **Knowledge base:** `data/knowledge_base/tricks.json` v0.1.0 holds 8 tricks, 45 steps, 29 coach signals, 29 failure modes and 15 source references. `pipeline/analyze.py --validate` passes. All entries are 1A and traceable to named source videos.
- **Verified architecture:** two separate pipelines. An offline build-time pipeline turns tutorial transcripts into the knowledge base; an on-device real-time pipeline is intended to watch a throw and coach it. Only the first exists.
- **Not implemented:** the entire vision stack (hand tracking integration, yoyo detector, string path estimation, signal extraction), the coach layer (state machine, failure-point locator, diagnosis engine, score engine), and the application itself. These are designed and diagrammed in `docs/architecture.html`; none of it runs.
- **Design artefacts only:** `docs/architecture.html` (MVP architecture) and `prototype/feedback-screen.html` (a static mock of the coaching screen, using the real Trapeze entry). Neither is wired to anything.
- **Known critical unknown:** detecting the yoyo and the string path. Body and hand pose estimation is off the shelf; this is not. Comparable research (skateboard trick classification, 2023) reached only 36% accuracy on limited data. The labelled dataset is the moat, not the model.
- **Known content risk:** auto-generated captions mangle yoyo vocabulary — `barar roll`, `bear roll`, `trapase`, `friend style bind` (front style bind), `the vine` (bind). See YO-002. The human curation gate currently covers this by review; it is not yet automated.

## Resume here

Do not rebuild the content pipeline; it works. Do not treat the architecture diagram or the prototype screen as implemented functionality.

1. Run `python pipeline/fetch_transcripts.py` and `python pipeline/analyze.py --validate` first to confirm the baseline still passes before changing anything.
2. Decide repository publication (public or private) with Kavi, then add the remote and push. Do not create a second copy of the project elsewhere.
3. Resolve YA-00E — confirm the single v1 trick and the camera angle — before writing any detector code. Everything in M2 depends on this.
4. Start M2 with the capture harness (YA-20A) and hand tracking (YA-20B), which are low risk, then attack the yoyo detector (YA-20C), which determines whether the product is possible at all.
5. Keep the `coach_signals` gate enforced. A trick added without signals must fail validation rather than silently ship as content the camera cannot check.

Authoritative baseline: knowledge base v0.1.0, 16 cached transcripts, manifest `ok: 16`. No commit history exists yet because the project is not a git repository.

## Milestone tracker

Allowed status values: `not_started`, `in_progress`, `blocked`, `done`. Only use `done` with evidence that the milestone's exit gate passed.

| Milestone | Status | Tasks | Evidence / blocker |
|---|---|---|---|
| M0: Discovery and feasibility | in_progress | YA-00A–YA-00E | A/B/C/D complete with cited findings; YA-00E (v1 trick and camera angle) awaits a decision from Kavi |
| M1: Content pipeline | in_progress | YA-10A–YA-10G | A–D done and validated; trick set still narrow (8 tricks, all 1A), curation not automated, caption normalisation outstanding |
| M2: Vision stack | not_started | YA-20A–YA-20F | Blocked by YA-00E. Highest risk in the project |
| M3: Coach layer | not_started | YA-30A–YA-30D | Depends on M2 signal extraction |
| M4: Application and experience | not_started | YA-40A–YA-40D | Prototype screen exists as a design reference only |
| M5: Hardening and release | not_started | YA-50A–YA-50D | Depends on M2–M4 |
| M6: Expansion | not_started | YA-60A–YA-60E | Depends on M5; 4A offstring is the hardest observation problem |

Use the plan's checkboxes as the complete task list. Add active-task rows here as work starts rather than maintaining two competing copies of every checkbox.

## Active tasks

| Task | Status | Owner | Latest evidence | Next action |
|---|---|---|---|---|
| YA-00E | in_progress | Kavi | v1 trick and camera angle not yet chosen | Pick one trick (Trapeze is the plan's default) and one angle |
| YA-10E | not_started | Implementer | 8 tricks, all 1A | Widen to the full 1A beginner ladder, then intermediate |
| YA-10G | not_started | Implementer | YO-002 open; garbled caption terms confirmed in fetched transcripts | Add a term-normalisation pass before analysis |
| Repo publication | not_started | Kavi / Implementer | No remote configured, no GitHub repository exists | Decide visibility, then create and push |
