# Build report: data-driven site, API and admin panel

Date: 2026-10-07. Environment: Linux sandbox, PostgreSQL 16.15, Node (sandbox version), headless Chromium with software WebGL.

## Verified results (all run on the final code)

| Suite | Result |
|---|---|
| API tests (`server/test/api.test.js`, real PostgreSQL) | 14 / 14 pass |
| End-to-end browser tests (`tests/e2e/e2e.py`) | 12 / 12 pass (before the final cosmetic CSS fix to the admin "View site" link; API tests were rerun after it) |
| Original-behavior regression (`tests/baseline/baseline.py index.html`) | 30 / 30 pass, offline-fallback path (no API available) |
| Drive Mode auto tour on the new page | pass: 7 stops then "Tour complete" |

What the tests cover: migrations from an empty database; public API returns only published content and no private fields; anonymous admin calls get 401;
OTP rules (allowed email only, 5-attempt lockout, 60-second resend cooldown, one-time use, code stored as a keyed hash); HttpOnly + SameSite=Strict session cookie;
CSRF token and Origin checks; section/item create, update, reorder, hide, move, delete (with cascade); input validation including `javascript:` links;
SQL-injection text stored inertly; reserved page ids cannot be used as section slugs; audit log; logout revokes the session;
the admin UI end to end (sign in, add a section and an item, public site shows 8 sections, Drive Mode builds 8 roads and fast-travels to the new street,
delete, sign out); hostile HTML in a title renders as text.

## Bugs found by testing and fixed during this build

1. Drawer buttons were rendered too late for the original click bindings, which stopped the script (caught by the browser test).
2. The typewriter started before content loaded and crashed on an empty phrase list (caught by the browser test).
3. Section slugs could collide with existing page element ids (now prefixed, with a test).

## Intentional behavior changes from the prototype

* "Admin Login" now opens `/admin/` instead of a stub modal (the modal markup is left in the file, unused).
* Content comes from the API; the embedded copy is the fallback if the API is unreachable.
* Sections are no longer fixed at seven (see limits below).
* Accordion rows appear only for items that have "expanded details"; items without details are plain rows.
* Item text is HTML-escaped everywhere it is rendered, including Drive Mode panels.

## Known limits and untested items (please read)

* **Email:** sending the login code through the real Brevo API has **not** been tested (no key/network here). The Brevo request is covered only by code review; the dev log path is what the tests use.
* **Hosting and managed Postgres:** not deployed anywhere. Tested only against a local PostgreSQL 16. Providers that require SSL may need `?sslmode=require` in `DATABASE_URL`; untested.
* **More than 7 sections:** the 3D roundabout geometry was not rescaled. Eight sections were tested functionally (roads built, driving, fast travel) but not judged visually.
* **Single admin:** one allowed email from `ADMIN_EMAIL`; rate limits are in memory (per server instance); sessions last 8 hours.
* **CSP** allows inline scripts/styles because the page is one large inline script; this limits the protection it gives against XSS.
* **Public cache:** content changes can take up to ~30 seconds to show.
* **Admin UI:** forms only. No drag-and-drop, image upload, draft preview or unsaved-changes warning. Not accessibility-audited.
* **Performance:** frame times from software rendering are not representative of real devices. Only Chromium was tested.
* **Not built:** contact form and stored messages, email notifications, analytics and consent notice, AI assistant/RAG, deployment, backups.
