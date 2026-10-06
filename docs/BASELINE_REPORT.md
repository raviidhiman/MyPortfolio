# Phase 1 baseline report

Date of run: 2026-10-06. Target: `index.html`, verified byte-identical to the original
(SHA-256 `748a091d834bc789644a7c91df25fa03899a244aef806147ce78f3934ca5fdaa`). **No site code has been changed.**

## What was run

* `tests/baseline/baseline.py`: 30 checks. Result: **30 passed, 0 failed** (`tests/baseline/results.json`).
* `tests/baseline/autotour.py`: auto tour. Result: **passed** (visited About, Skills, Projects, Experience, Education, Research, Contact, then "Tour complete"; 285 s wall time under software GL).
* 36 baseline screenshots in `tests/baseline/screenshots/` (3 viewports x home + 7 sections + drawer; Drive chooser, driving, detail panel, 4 camera modes, mobile landscape, tour complete). I viewed two of them (desktop home, Drive detail panel) to confirm they show the real design and 3D scene.

## Performance baseline (indicative only)

42 frames in a 6 s hold-W drive, frame time p50 150 ms, p95 183 ms, 0 script-initiated network calls (fetch, XHR, beacon, WebSocket).
These are **software-rendered** numbers (SwiftShader, no GPU) in a sandbox, so they say nothing about real-device FPS.
Use them only to detect a before/after change on the same machine. An earlier run made while a second browser ran concurrently
gave 350 ms; it was discarded as contaminated.

## What this does and does not establish

Established: every listed interaction works in Chromium on the unmodified prototype; the render loop makes no network calls; the page loads with no console errors; mobile 390px has no horizontal overflow.

Not established: pixel-level parity (no diff tool yet), real GPU performance, Firefox/Safari/iOS, audio, free-driving collision feel, real keyboard/screen-reader behavior.
D6 positions the car via internal state rather than by driving to the sign (the auto tour covers real driving).
Test coverage is behavioral smoke coverage, not exhaustive.

## Baseline defects found (recorded, not fixed)

1. CDN/WebGL failure uses a blocking `alert()` (Blueprint requires a graceful path).
2. `window.claude.use('sample')` does not exist outside Claude artifacts; the search silently falls back to retrieval text.
3. axe-core: 1 moderate issue, rule `region` (content outside landmarks). Informational scan only; it is not a full accessibility audit.
4. Code-level observations (verified by search of the source, not by a behavioral test): no focus trap or focus return for the drawer, modal and Drive overlay (the only `.focus()` call is on the search box); Drive code never consults `prefers-reduced-motion`.

## Proposed Phase 2: verified content (needs your go-ahead and decisions)

Scope: replace placeholders in `S` with content from the content doc, wire the real social links and email, add `confirm` flags, and
create an editable `content.seed.json` for later phases. No layout or CSS changes. Section ids, `street` names and count stay fixed.

Before Phase 2 I need answers to the open confirmations in `CONTENT_RECONCILIATION.md`, chiefly:
(1) show CONFIRM-flagged facts publicly with a flag, or hold them back; (2) the research conflict, with the PDF uploaded if I cannot fetch it;
(3) featured project order and which extra projects to include; (4) headline wording.

Phase 2 re-runs the baseline; tests that assert placeholder text will change by design and will be updated and listed explicitly,
so a changed expectation is never hidden as a pass.
