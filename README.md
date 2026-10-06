# Ravi Dhiman portfolio: phased build

Status: **Phase 0 and Phase 1 complete.** The site itself (`index.html`) is still the unmodified original prototype.
Nothing from Phases 2 to 11 (content, database, API, contact, auth, admin, analytics, RAG, integration, deployment) has been built yet.

## Layout

| Path | Purpose |
|---|---|
| `original/portfolio-fixed__2_.html` | Pristine original (never edit) |
| `index.html` | Working copy; currently byte-identical to the original |
| `docs/PHASE0_REPORT.md` | Inventory, architecture, risks |
| `docs/CONTENT_RECONCILIATION.md` | Prototype vs content doc; open confirmations |
| `docs/BASELINE_REPORT.md` | Phase 1 results, limits, known defects, Phase 2 proposal |
| `tests/baseline/` | Harness (`baseline.py`, `autotour.py`), results JSON, checklist, 36 screenshots |
| `tests/vendor/` | Three.js r128 and axe-core, used only so tests run offline |
| `.git` | Commit history (one commit per phase) |

## Run the baseline

Requires Python 3, `pip install playwright`, then `python3 -m playwright install chromium`.

    python3 tests/baseline/baseline.py                 # about 4 min; writes tests/baseline/results.json
    AUTOTOUR_BUDGET=900 python3 tests/baseline/autotour.py   # about 5 min

Run both before and after each phase and compare with `tests/baseline/REGRESSION_CHECKLIST.md`.
Use `BASELINE_PORT=NNNN` to avoid port clashes when running two at once. Results are reported as measured; software-rendered
timings are indicative only.

## Not yet in this project

No backend, database, `.env.example`, deployment config, or API docs exist yet. They belong to later phases.
No secrets are present anywhere in this archive.
