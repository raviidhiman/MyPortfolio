# Ravi Dhiman portfolio: full-stack site with admin panel

A working website: the public portfolio (with the original 3D Drive Mode) reads its content from a PostgreSQL database
through a Node/Express API, and you manage everything from `/admin`.

## What you can manage from /admin (all built and tested)

* **Sections:** add, rename, reorder, hide, delete whole sections (title, street name used in Drive Mode, colour, icon, layout).
* **Content:** add, edit, reorder, hide, delete items inside any section, and move an item to another section.
* **Project buttons:** each item has optional **Live**, **GitHub** and **Docs** links (Docs is a link to a PDF / Google Doc / Notion page; file upload is not built). A small button appears on the site only for links you fill in; clicking the project box or + only expands it.
* **Site & hero:** browser title, search description, greeting, name, typing phrases, hero paragraph, button label, and the social/contact icons.
* **Activity:** audit log of every change and sign-in.
* Sign-in is by one-time code emailed to `ADMIN_EMAIL` only: the login page shows just **Admin Login** and a **Send code** button (no email field), a Resend button unlocks after 30 seconds, and a small back arrow returns to the site. Changes appear on the public site within about 30 seconds.
* **Messages** tab: every contact-form message, a **Send chat invite** button (e-mails the visitor a private chat link) and a live chat you can close at any time.

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
    python3 tests/e2e/cockpit.py                                  # cockpit, 540-degree wheel, wheel/body physics, coins, engine loudness (needs: git show HEAD~1:index.html > /tmp/old.html)
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

## Drive Mode (cockpit)

Drive Mode now starts in a cockpit view: body-colour hood, speedometer, fuel gauge (cosmetic), blinking indicators, hazard triangle and P/R/N/D (cosmetic),
a steering wheel that turns 1.5 rounds each way, ribbed brake and gas pedals, front wheels that steer and spin, body roll and nose dive,
and 5 collectible coins per road with a live counter. Press the camera button to switch to chase or hood views.

## Not built yet

Contact form with stored messages and email notification, visitor analytics and consent notice, AI assistant over your content
(LLM/RAG; the search box now uses a rule-based answer composer, not an AI model), document file upload, deployment to a live host, and real-Brevo / real-LLM verification. The page's search box still uses on-page retrieval only.
The seed/fallback content is the profile document as written; fields it marked "confirm" are shown without badges, as you asked.

## Drive Mode v2 (Alps map, real cars, Lamborghini wheel)

* **Map:** `assets/map.glb` (Chamonix Alps track, textures shrunk to 1024px). The seven sections are checkpoint gantries with a light beam placed along the map's centre route, in section order. Drive through a gantry to open its details; the minimap shows the route and numbered stops; the bolt button fast-travels to any stop; Auto tour drives the whole route.
* **Car:** G-Class (`gclass.glb`). The Sedan (Cutlass 71) and the car-change button were removed.
* **Cockpit:** three cameras (C or 1-3): close chase, far chase and a bonnet view. The Lamborghini steering wheel (`wheel.glb`) sits bottom-right and turns 1.5 rounds each way; drag it on touch screens. Both pedals are bottom-left. Tyres spin with speed and the front wheels steer.
* **Physics:** the car follows the real terrain (ray-cast ground), pitches on slopes, is slowed off-road and blocked by walls and map edges.
* **Sound:** engine rebuilt with smooth gear/rpm changes, no hard compressor, lower master level.
* Section titles no longer show road names on the main page (the `street` field is simply unused now).
* Serve `assets/` next to `index.html`. `GLTFLoader.js` is bundled; Three.js still loads from cdnjs.
* The old cockpit/physics tests in `tests/` target the previous roundabout world and will need updating.

* Build 5: auto tour cruises at 120 km/h (slows for tight bends, no post-checkpoint speed lock); speedometer shows true km/h; camera snaps behind the car on start; all cockpit/coin remnants removed.
* Build 6: smoother ground following (5-point averaging, camera smoothing, body roll), better depth precision (less map flicker), no off-road slowdown, Research checkpoint moved ~120 m from the bridge.
* Build 7: car can no longer sink into the ground (height floor from the ground under it), smoother pitch/throttle, auto-tour checkpoint prompt is 2.5 s and says "Next checkpoint", more robust checkpoint arrival (no circling).


## AI search + assistant (RAG), security and speed (build 8)

**How the assistant works** (`server/rag.js`)
1. Your *published* sections, items and hero/social settings are copied into a PostgreSQL search index (`rag_chunks`). Drafts and admin data are never indexed. It rebuilds automatically ~1.5 s after any admin change (and on server start).
2. A visitor question is checked (length, control characters, prompt-injection / secret-seeking patterns), then the best matching chunks are retrieved with PostgreSQL full-text search.
3. Only then is your model called, **from the server**, with a strict prompt: answer only from CONTEXT, treat CONTEXT and QUESTION as untrusted data, plain text, max ~90 words. If nothing matches, or the question is refused, the model is **not called**.
4. If the model is not configured, fails, or the daily limit (`LLM_DAILY_LIMIT`) is hit, the visitor still gets a useful search-based answer.
* `POST /api/assistant/query` `{q}` -> `{mode: ai|search|none|refused, answer, sources}` (12 requests / 10 min / IP)
* `GET /api/search?q=` -> ranked snippets (60 / min / IP)
* Admin only: `POST /api/admin/rag/reindex`, `GET /api/admin/rag/status` (never returns keys).

**Configure the model:** copy `.env.example` to `.env` (project root), then fill `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` from your provider's documentation. Restart the server. The key must never be pasted into chat, code, `index.html` or git. If a key was ever shared publicly, revoke it and create a new one.

**Security changes**
* Admin e-mail is never pre-filled, never hard-coded and never returned by any API; it is set only via `ADMIN_EMAIL` and stored only as a keyed HMAC. OTP codes are HMAC-hashed. Session tokens are SHA-256 hashed. The CSRF token is derived from the session and not stored.
* Each login revokes every older session and starts a new one. The cookie is a browser-session cookie (`__Host-sid`, HttpOnly, Secure, SameSite=Strict in production), the server expires sessions after 20 min idle / 2 h total, and logout revokes all sessions and reloads the admin page.
* Admin API responses are `Cache-Control: no-store`; public content no longer exposes internal database ids. Added Permissions-Policy, COOP/CORP, HSTS (production), a 20 KB JSON body limit and stricter rate limits.
* Note: anything a browser *receives* is visible in its Network tab by design. The protection is that the browser is never sent secrets (keys, e-mail allow-list, hashes, internal ids) and that admin data requires a valid session.

**Speed**
* gzip for HTML/API/3D files (HTML 95 KB -> 34 KB), 30-day immutable caching for versioned 3D assets, revalidating `index.html`, stale-while-revalidate for content.
* 3D models re-saved with compact vertex data (map download 8.9 -> 6.3 MB, G-Wagon 5.4 -> 2.2 MB, Cutlass 3.1 -> 2.2 MB after gzip) and expanded to floats at load.
* The map, G-Class and wheel are pre-fetched in the background (hover/touch on the Drive button, or after 7 s idle on a fast non-metered connection) so entering Drive Mode is near-instant.

Run all server tests (needs PostgreSQL, see `server/test/*.js`): `cd server && npm test`.

**xKiro setup:** `LLM_BASE_URL=https://api.xkiro.com/v1`, `LLM_MODEL=mistralai/mistral-large-4-0` (or another id from https://xkiro.com/models), `LLM_REASONING_EFFORT=none`, `LLM_API_KEY=` your key.

## Build 9
* Two cars only: G-Class and Sedan (Cutlass). New 4th camera **Wheel · 360°**: orbits the front wheel while stopped (drag to rotate), glides to a side-on view as you drive so you can watch the tyre spin and steer. Keys 1-4 / C.
* Lightning button / minimap: opens the checkpoint list with a highlighted **Next** (key **N** jumps straight to the next checkpoint).
* Auto tour now starts from where you are: it continues with the next checkpoint ahead of you (and restarts from About only after the last stop). If you are off the road or facing backwards it re-seats you on the route first.
* RAG: every field of every item (description, details, GitHub / live / document links), all settings, contact details and a section overview per section are indexed. The model receives the **whole portfolio** as context on every question (set `LLM_FULL_CONTEXT_CHARS` to change the 60 000-character threshold), so nothing you added can be "unknown". Answer links are clickable.

## Deploy (GitHub + Render)
1. Create a GitHub repo and push this folder. `.env` is git-ignored: never commit it.
2. Render -> **New + -> Blueprint** -> choose the repo (it reads `render.yaml`), or **New Web Service** with build `cd server && npm ci`, start `cd server && node index.js`, health check `/api/health`.
3. Set the environment variables in the Render dashboard: `DATABASE_URL`, `ADMIN_EMAIL`, `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `LLM_API_KEY` (and `OTP_SECRET` is generated for you). `NODE_ENV=production` is already set.
4. Brevo: authorize Render's outbound IPs (see Render docs) or deactivate IP blocking in Brevo -> Security -> Authorized IPs, otherwise login e-mails are rejected.
5. Open `https://YOUR-APP.onrender.com/admin/`, sign in, add content; the AI index refreshes by itself.
* Render's free plan sleeps after inactivity (first visit after a break takes ~30-60 s). A paid instance keeps it awake.
* Vercel is not a good fit: this app is a long-running Express server with a database pool; Vercel needs it rewritten as serverless functions.

## Build 10: engine sound (your clips)
Sampled clips in `assets/sounds/` replace the old synthesized engine. The mapping (`audioUpd` in `index.html`):
| Situation | Clip |
|---|---|
| Click "Enter game mode" | `1_ignition_start` (once) |
| Car standing still | `1b_ignition_g63_coldstart` (idle loop) |
| Accelerating | `2a_accelerate_pull` (pitch rises with speed) |
| Throttle held, speed steady | `2b_accelerate_sustained` |
| Lifted off, rolling at constant speed | `3_cruise_loop` |
| Brakes on / losing speed | engine-brake note made from `3_cruise_loop`, low-passed, pitch and brightness fall with speed + synthesized brake-pad noise and a faint squeal near a stop |
| Car comes to a stop | synthesized soft thump + brake-air release (once) |
| Sliding / drifting | synthesized tyre squeal + scrub, louder with slip |
| Reversing | `2a_accelerate_pull`, low and slow, follows reverse speed |
Every loop is cross-faded so it repeats without a click, and the sound button mutes everything. Add or replace clips by keeping the same file names in `assets/sounds/`.

## Build 11
* **Volume:** starts at 35% (about 3x quieter than before). Change it three ways: tap the speaker icon in the game (15% > 35% > 60% > 100% > off), press `-` / `+`, or edit `VOL_DEFAULT` near the top of the sound code in `index.html` (0 to 1). The choice is remembered in the browser.
* **Orbit 360 camera** (key 4): far-chase distance (15 m). While stopped it orbits slowly (drag to turn it). Driving forward it eases round to behind the car; reversing it eases round to the front.

## Render + Supabase troubleshooting
* `ENETUNREACH ... 2406:...:5432` = you used Supabase's *direct* address (IPv6 only). Use the **Session pooler** string (Supabase -> Connect -> Session pooler): `postgresql://postgres.PROJECTREF:ENCODED_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require&uselibpqcompat=true`. The user name is `postgres.PROJECTREF`, not just `postgres`. Percent-encode special characters in the password.
* Node is pinned to 22 (`server/package.json` engines + `.node-version`) so Render does not pick the newest release.

## Build 12
* **Drift:** hold the **Brake** (Space / Shift / S, or the on-screen brake pedal) at speed while steering; straight braking is a plain stop. There is no separate Drift button any more. Normal driving and the auto tour are unchanged (full grip); the handbrake loosens the rear end, giving a controllable slide with tyre smoke, skid marks and tyre squeal. The chase camera leans into the slide, the speedometer shows true speed. Tune the feel in the `DRIFT` block near the top of the drive code in `index.html` (grip, turn-rate boost, how hard the tyres bite as the slide grows, speed scrub, handbrake braking).
* **Sounds:** the two clips `4_slowing_down` and `5_braking_engine_drop` were removed; braking, slowing, stopping and tyre squeal are synthesized in the browser.
* **Phones:** the nav bar shows only search + menu (30% shorter); landscape steering wheel is twice as big on touch devices; the sedan's front wheels no longer twitch (steering shown smoothly).
* **Full screen:** small button in Drive Mode only (hidden on iPhone, which has no page full-screen).
* **360 camera:** does not auto-rotate when stopped; still settles behind (forward) / in front (reverse) when moving.
* **Branding:** tab title is `Ravi Dhiman`; favicon set in `assets/icons/` (migration 004 renames the stored title on an existing database only if it still has the old default).
* **Nav bar:** transparent at the top of the page, lighter dark glass once you scroll.

## Build 13
* Small screens (up to 768 px): the nav bar shows only a magnifying glass and the menu button. Tap the glass: the search box opens, grows with the question as you type and stops at the middle of the nav bar; it closes after searching, on Escape, or when you tap away from an empty box. Desktop keeps the full search box and links.


## Pages, contact and drive update (latest)
* **One page per section.** The landing page scrolls exactly as before. Picking a section in the burger menu opens its own page (`/about`, `/skills`, ... built from the same data and styling, so sections you add in admin get a page automatically). Every page has a **Back** button; Drive Mode's *Open full page* opens that section's page and a **Back to Drive** button resumes the game at the exact spot (position, heading, camera and gear are kept in the browser session).
* **Connect / Reach out** (`/connect`): contact form + WhatsApp button (`WHATSAPP_NUMBER`). It is in the burger menu and as a small toggle at the bottom of the Contact section. Each message is saved, e-mailed to `ADMIN_EMAIL` (reply-to is the visitor) and listed under **Messages** in admin, where **Send chat invite** e-mails a private `/chat/<token>` link. You can close a chat any time; a closed chat is read-only for the visitor. You also get at most one "new chat message" e-mail per chat every 10 minutes. Anti-spam: hidden trap field, 5 messages per hour per IP, 100 per day overall.
* **Drive controls.** Brake only brakes (never reverses). Brake + steering at speed drifts. A P-R-N-D gear selector sets the direction: D forward, R reverse, N coast, P park (D/R/P only change when nearly stopped). Keys: `R` `F` `X` `P`. The gear knob fades out above 25 km/h and returns below 20 km/h. Pedals are redrawn as crisp SVG.
* **SEO.** `/sitemap.xml` and `/robots.txt` are generated from your published sections (set `SITE_URL`). Submit `https://YOUR-SITE/sitemap.xml` in Google Search Console. The verification meta tag is in the `<head>` of every page. `android-chrome-192x192.png` is the only favicon everywhere.
* New migration `005_contact_chat.sql` (runs automatically on start). New env values: `SITE_URL`, `WHATSAPP_NUMBER`.
