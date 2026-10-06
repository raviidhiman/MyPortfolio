# Regression checklist (Phase 1 baseline)

Run before and after every phase: `python3 tests/baseline/baseline.py` (about 4 minutes) and, for the
auto tour, `AUTOTOUR_BUDGET=900 python3 tests/baseline/autotour.py` (about 5 minutes).
Results are written to `tests/baseline/results.json` and `autotour-result.json`.
Environment: headless Chromium, software WebGL (SwiftShader), Three.js r128 served locally from
`tests/vendor/` (the sandbox cannot reach cdnjs). `Math.random` is seeded so the 3D scene is repeatable.

## A. Automated (recorded in results.json)

| ID | Check | Baseline |
|---|---|---|
| N1 | Loads; h1 "Ravi Dhiman"; 7 sections; no console or page errors | PASS |
| N2 | Nav "Contact" brings `#contact` fully into view (last section; page bottoms out) | PASS |
| N2b | Nav "Home" scrolls to top | PASS |
| N3 | Drawer opens; closes by Esc, outside click, and link navigation | PASS |
| N4 | Accordion rows toggle by click, Enter, Space (with `aria-expanded`) | PASS |
| N5 | Search: answer + section chips; no-hit message; Esc clears | PASS |
| N6 | Guided tour starts and stops on user scroll | PASS |
| N7 | Typewriter animates when motion is allowed | PASS |
| N8 | mailto row shows the copy toast | PASS |
| N9 | External links have `target=_blank` and `rel` containing noopener | PASS |
| N10 | Admin-login stub modal opens and closes | PASS |
| N11 | Scroll progress bar and section dots update | PASS |
| N12 | Reduced motion: typewriter shows static full text | PASS |
| N13 | Mobile 390px: no horizontal overflow | PASS |
| S1 | Screenshots: desktop 1440x900, tablet 820x1180, mobile 390x844 (home, 7 sections, drawer) | captured |
| A1 | axe-core scan (informational) | 1 moderate: `region` (x1) |
| D1 | Drive Mode starts; chooser shown; page scroll locked | PASS |
| D2 | WebGL canvas renders non-blank | PASS |
| D3 | W accelerates; Space brakes | PASS |
| D4 | C cycles 4 camera modes | PASS |
| D5 | Fast travel (button and mini-map) lands on Projects Street | PASS |
| D6 | Near sign: info pill, detail panel, Keep driving (position set via internal state) | PASS |
| D7 | "Open in Normal Mode" exits Drive and scrolls to the section | PASS |
| D8 | Car switch and sound toggle | PASS |
| D9 | **No network calls during the render loop** (fetch/XHR/beacon/WebSocket) | PASS (0) |
| D10 | Esc exits Drive Mode and restores scrolling | PASS |
| D11 | No console or page errors during a Drive session | PASS |
| D12 | Auto tour visits all 7 stops and reaches "Tour complete" | PASS (separate runner) |
| D13 | Touch device: pedals visible; GAS accelerates | PASS |
| F1 | CDN blocked: stays in Normal Mode, but via a blocking `alert()` | PASS (baseline defect, see below) |
| F2 | No `window.claude` runtime: search still answers via retrieval | PASS |

## B. Known baseline defects (recorded, not fixed)

1. **F1** CDN/WebGL failure uses a blocking `alert()`. Blueprint wants a graceful message. Fix in Phase 9.
2. The AI answer path depends on `window.claude.use('sample')`, which does not exist outside Claude artifacts. Search silently falls back to showing retrieved text. Replaced in Phase 8.
3. axe `region` (moderate): some content is not inside a landmark.
4. Code observations **not yet verified by a test**: no focus trap or focus return for the drawer, modal and Drive overlay; Drive Mode ignores `prefers-reduced-motion`.

## C. Manual-only (not covered by the harness)

* Pixel comparison against the original. Screenshots are stored for a manual or scripted diff after each phase. No diff tooling is set up yet.
* Real GPU frame rate. Baseline p50/p95 frame times are software-rendered numbers and are only meaningful for before/after comparison on the same machine.
* Engine and crash audio, steering-wheel drag, free-driving collisions against buildings, and real-device touch gestures.
* Real keyboard focus order and screen-reader behavior.
* Safari/iOS and Firefox. Only Chromium has been run.
* The pedals show on desktop as well as touch (`.tc{display:flex!important}`); this is the prototype's design and is preserved.
