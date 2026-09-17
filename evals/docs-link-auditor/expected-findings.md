# Expected findings

Target: `evals/docs-link-auditor/fixture/docs`. A correct audit must report at least:

## Broken links
1. `index.md` → `archive-order.md` does not exist.
2. `create-order.md` → anchor `track-order.md#tracking-steps` — `track-order.md` exists but has no "Tracking Steps" heading (heading is "Steps").

## Missing assets
3. `create-order.md` → `videos/create-order.mp4` does not exist.

## Orphaned assets
4. `images/unused-diagram.png` is referenced by no page.

## Navigation mismatches
5. `.pages` lists `complete-order.md`, which does not exist.
6. `track-order.md` exists (fine) — but `archive-order.md` linked from the index is absent from disk, already covered by finding 1.

## Verdict
Overall: fail (broken links and missing assets present).

False-positive check: `index.md ↔ track-order.md` links, `images/overview.png`, and `images/create-form.png` must not be flagged.
