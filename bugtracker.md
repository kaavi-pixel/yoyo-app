# yoyo-app Bug Tracker

Updated: 2026-10-22. Repository: [kaavi-pixel/yoyo-app](https://github.com/kaavi-pixel/yoyo-app) (public, default branch `main`).

This tracker records reproducible defects, fixes, and verification. Feature work remains in `implementation-plan.md`; a missing planned feature is not automatically a bug. Nothing here has been released, so no defect can be marked `released` or `verified_production`.

## Conventions

Statuses: `open`, `in_progress`, `fixed_local`, `released`, `verified_production`, `deferred`. `released` means the fix is deployed, but its specific failure case has not necessarily been reproduced safely in a release build. Severity: `critical` breaks the core product promise or risks data loss; `high` breaks core behaviour; `medium` affects a limited path or corrupts the knowledge base; `low` is cosmetic or internal.

Keep IDs stable. Every fix should include reproduction steps, changed modules, regression evidence, commit or release reference, and remaining verification. Do not close an issue based only on a single manual run — add it to the verification scenarios in `implementation-plan.md`.

## Defects

| ID | Severity | Status | Summary | Verification impact |
|---|---|---|---|---|
| YO-001 | low | fixed_local | Repeat transcript runs rewrote `ok` manifest entries as `cached`, so the success count decayed to zero and previously fetched sources appeared never fetched | Manifest now holds at `ok: 16` across consecutive runs |
| YO-002 | medium | open | Auto-generated captions garble yoyo vocabulary, so the analysis step can misread technique from the transcript | Not yet mitigated; current coverage is manual review only |
| YO-003 | low | open | `analyze.py --prompt` silently degrades to an empty schema when the knowledge base is absent | Not yet mitigated |

### YO-001: Manifest status regression on cached runs

- **Reproduction:** Run `python pipeline/fetch_transcripts.py` once (all sources fetch), then run it again with every transcript already cached.
- **Previous behaviour:** Cached sources were written back to the manifest with `status: "cached"`. The `ok` count therefore dropped as the `cached` count rose, and after a second run the manifest reported `{'ok': 0, 'cached': 16, 'failed': 0}` — the opposite of the truth. The skip logic also derived a stale `done_ids` set that no longer matched what was on disk, and printed that stale count as "already cached".
- **Fix:** Cached sources now report `status: "ok"` and carry forward their original `fetched_at`, `url`, `language` and `segment_count` from the cached payload. The "already cached" line counts `.json` files on disk rather than trusting the manifest, and the `cached` status was removed from the counts entirely in favour of `sources_registered`.
- **Modules:** `pipeline/fetch_transcripts.py`.
- **Evidence:** Two consecutive runs each report `{'ok': 16, 'failed': 0, 'sources_registered': 16}`, and `data/transcripts/manifest.json` holds 16 entries. Previously the second run reported `ok: 0`.
- **Remaining:** A schema version field on the manifest would let future format changes be detected rather than silently misread.

### YO-002: Auto-captions garble yoyo terminology

- **Reproduction:** Inspect the fetched transcripts for yoyo-specific terms.
- **Observed behaviour:** Auto-generated captions consistently corrupt the vocabulary the analysis step depends on. Confirmed in the current corpus: `barar roll` (barrel roll), `bear roll` (barrel roll), `trapase` (trapeze), `friend style bind` (front style bind), `the vine` (bind). Captions also drop technical nouns mid-sentence and merge words across segment boundaries.
- **Impact:** The analysis step is an LLM reading this text. A garbled mount name can become a fabricated step or a wrong failure mode, which would then be presented to a player as instruction. Because the knowledge base is the product's ground truth, this is a correctness risk, not a cosmetic one.
- **Current mitigation:** The human curation gate. Every entry is reviewed against the transcript, and the plan's traceability scenario requires each statement to resolve to a source video. This works but does not scale and is not automated.
- **Planned fix:** A normalisation pass before analysis — a yoyo term dictionary mapping observed mis-hearings to canonical terms, applied to transcript text and recorded so the raw transcript remains untouched. Tracked as YA-10G.
- **Modules:** `pipeline/analyze.py` (pre-processing), `pipeline/sources.json` (term dictionary).
- **Remaining:** Not started. Also worth preferring human-authored captions over auto-captions in the source registry where the choice exists.

### YO-003: Silent schema fallback in the prompt builder

- **Reproduction:** Delete or rename `data/knowledge_base/tricks.json`, then run `python pipeline/analyze.py --prompt "Trapeze"`.
- **Observed behaviour:** `build_prompt` reads the knowledge base only to embed the schema, and falls back to an empty object when the file is missing. The prompt is then emitted with `"Return ONLY JSON matching this schema:"` followed by `{}`, which would teach the model nothing about the expected shape. There is no warning.
- **Impact:** Low today, because the knowledge base is committed. It becomes a silent quality regression if the analysis step is ever run before the knowledge base exists, or in a fresh checkout where it was not restored.
- **Planned fix:** Fail loudly with a clear message when the schema cannot be loaded, rather than emitting a degenerate prompt.
- **Modules:** `pipeline/analyze.py`.
- **Remaining:** Not started.
