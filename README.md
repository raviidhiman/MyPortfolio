# Ravi Dhiman portfolio: full-stack site with admin panel

A working website: the public portfolio (with the original 3D Drive Mode) reads its content from a PostgreSQL database
through a Node/Express API, and you manage everything from `/admin`.

## What you can manage from /admin (all built and tested)

* **Sections:** add, rename, reorder, hide, delete whole sections (title, street name used in Drive Mode, colour, icon, layout).
* **Content:** add, edit, reorder, hide, delete items inside any section, and move an item to another section.
* **Project buttons:** each item has optional **Live**, **GitHub** and **Docs** links (Docs is a link to a PDF / Google Doc / Notion page; file upload is not built). A small button appears on the site only for links you fill in; clicking the project box or + only expands it.
* **Site & hero:** browser title, search description, greeting, name, typing phrases, hero paragraph, button label, and the social/contact icons.
* **Activity:** audit log of every change and sign-in.
* Sign-in is by one-time code emailed to `ADMIN_EMAIL` only. Changes appear on the public site within about 30 seconds.

Drive Mode builds one road per visible section. The original layout fits up to about 7 sections comfortably; with more, roads get
close together at the roundabout (they still work). Keep it to 7 to 9 for the best look.

## Run locally

    cd server && npm install
    bash ../tools/dev.sh            # starts PostgreSQL 16 (Linux), creates the dev DB, runs the server on :3100
    # site: http://localhost:3100/   admin: http://localhost:3100/admin/
    # in dev the sign-in code is printed in /tmp/server.log (no email is sent without BREVO_API_KEY)

On macOS/Windows, point `DATABASE_URL` at any PostgreSQL and run `node index.js` from `server/`.
Tables are created and your profile content is seeded automatically on first start (only if the database is empty).

## Tests

    cd server && npm test                                        # 16 API tests, real PostgreSQL (TEST_DATABASE_URL to override)
    E2E_URL=http://127.0.0.1:3100 E2E_LOG=/tmp/server.log python3 tests/e2e/e2e.py     # 12 browser tests (admin UI + public + Drive)
    python3 tests/e2e/features.py                                 # project buttons + 12 assistant questions (needs tools/dev.sh running)
    python3 tests/e2e/physics.py                                  # measures the page's own driving physics
    python3 tests/baseline/baseline.py index.html                # 30 regression checks of the original behavior (offline fallback path)
    AUTOTOUR_BUDGET=900 python3 tests/baseline/autotour.py       # Drive Mode auto tour

## Deploy (not yet done or tested on a real host)

1. Create a PostgreSQL database (Supabase, Neon or Render Postgres) and a Brevo account with a verified sender.
2. Set the variables in `.env.example` on your host (`NODE_ENV=production`, `DATABASE_URL`, `OTP_SECRET`, `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`).
3. Deploy the folder to any Node host; start command `node server/index.js` (run `npm install` in `server/`). Serve over HTTPS.
In production the server refuses to start without `OTP_SECRET` and never prints login codes.

## Layout

| Path | Purpose |
|---|---|
| `index.html` | Public site, derived from the original prototype by `tools/patch_index.py`; embedded content is the offline fallback |
| `admin/index.html` | Admin panel |
| `server/` | API (`index.js`), schema (`migrations/`), starting content (`seed.json`), API tests |
| `original/` | Pristine prototype (never edit) |
| `tools/` | `patch_index.py` (how the prototype was made data-driven), `dev.sh` |
| `tests/` | Baseline regression, end-to-end, vendored Three.js/axe for offline testing, screenshots |
| `docs/` | Phase 0 report, content reconciliation, baseline report |

## Not built yet

Contact form with stored messages and email notification, visitor analytics and consent notice, AI assistant over your content
(LLM/RAG; the search box now uses a rule-based answer composer, not an AI model), document file upload, deployment to a live host, and real-Brevo / real-LLM verification. The page's search box still uses on-page retrieval only.
The seed/fallback content is the profile document as written; fields it marked "confirm" are shown without badges, as you asked.
