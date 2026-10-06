# Phase 0 report: inventory, architecture, risks

Updated after the Website Content & Profile document was supplied. Companion docs:
`CONTENT_RECONCILIATION.md` (facts) and `../tests/baseline/REGRESSION_CHECKLIST.md` (tests).

## 1. File inventory

| File | Role |
|---|---|
| `portfolio-fixed__2_.html` (74,326 bytes, 495 lines) | Original prototype; source of truth for design and interaction. Preserved untouched in `original/`. |
| `Ravi_Dhiman_Portfolio_Blueprint_and_Master_Prompt.docx` | Implementation spec. |
| `Ravi_Dhiman_Portfolio_Blueprint_and_Master_Prompt__1_.docx` | Byte-identical duplicate of the above (same SHA/MD5). |
| `Ravi_Dhiman_Website_Content_and_Profile.docx` | Factual content source (supplied after the first Phase 0 report). |

No resumes or project READMEs were supplied. The content doc says its facts were synthesized from them, so claims in it that
point to those files (e.g. "README references roughly 96.5k delivered orders") could not be checked against the originals.

## 2. Current architecture and dependencies

* One file: one `<style>`, one inline `<script>`; no framework, no build step. JavaScript parses cleanly.
* Content model: `const S` (7 sections: About, Skills, Projects, Experience, Education, Research, Contact). It drives page markup,
  the nav drawer, the search index, and the Drive Mode roads, signs and panels.
* Only third-party runtime asset: Three.js r128 from cdnjs, loaded lazily on first Drive Mode entry, no integrity hash.
  No web fonts. No `fetch`, storage, or CSP in the prototype.
* Search: client-side BM25-style retrieval over `S`, then `window.claude.use('sample')` (exists only in Claude artifacts); falls back to showing retrieved text.
* Admin login: a stub modal that says no backend is connected (mentions Supabase).

## 3. Features that must not regress

Normal mode: hero typewriter, particle canvas, cursor spotlight, progress bar, section dots, drawer, accordions, search,
guided tour, copy-email toast, reduced-motion handling. Drive Mode: Three.js roundabout and 7 roads, 3 cars, 4 cameras,
keyboard/touch/wheel controls, collisions, mini-map and fast travel, sign panels, auto tour, synthesized audio, cockpit dashboard.
All are encoded in `tests/baseline/REGRESSION_CHECKLIST.md`.

## 4. Content discrepancies

See `CONTENT_RECONCILIATION.md`. Headline conflict: the prototype states the stroke-risk work is "not a published paper",
while the content doc supplies a publication PDF for the research section.

## 5. Recommended minimal architecture

* Frontend: keep the single HTML file; add a small integration layer that fetches `/api/public/content` once at load (outside the render loop) and re-renders. Embedded `S` remains the static fallback.
* Backend: Node LTS + Express. Database: PostgreSQL, migrations, parameterized queries. Email: Brevo HTTPS API.
* RAG: PostgreSQL full-text search first; deterministic fallback if no model is usable.
* Admin UI: separate `/admin` page reusing the existing CSS tokens, so the 3D page never carries admin code.
* Hosting: not chosen; official free-tier terms to be checked at deployment time (Phase 10).
* Constraints from the code: (a) section set is fixed at 7 because the 3D world is built from `S.length`; (b) a safe-render helper is needed
  because about 20 `innerHTML` sinks interpolate content unescaped, which is only safe while content is hardcoded.

## 6. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Unverified facts and the research conflict | High | CONFIRM flags; never invent; owner decisions listed |
| 2 | Unescaped `innerHTML` plus database content | High | Escape helper, URL allowlist (https/mailto), XSS tests |
| 3 | Contact form does not exist in the prototype | Medium | Add in the existing `.row`/`.btn` style; placement needs approval |
| 4 | CSP: one large inline script and many inline `style=` attributes | Medium | `'unsafe-inline'` or script hash (changes each edit) |
| 5 | Three.js from CDN without integrity; `alert()` on failure | Medium | Self-host r128 or add SRI; friendly message |
| 6 | Scene uses `Math.random` (9 calls); Drive visuals differ per run | Medium (tests) | Seeded in the harness |
| 7 | `claude.use` dependency | Low | Replaced by server-side RAG in Phase 8 |
| 8 | No focus trap/return for drawer, modal, Drive overlay; Drive ignores reduced motion | Low to Medium | Verify with tests in Phase 9/11 |
| 9 | No local Postgres in the sandbox | Low | Try apt; else PGlite, with a caveat that final verification needs a real instance |

## 7. Baseline test plan

Implemented in Phase 1; see `tests/baseline/` and `docs/BASELINE_REPORT.md`.
