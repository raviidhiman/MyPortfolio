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


## Round 2 (2026-10-07): project buttons, assistant answers, driving

Results on the final code: API tests 16/16, end-to-end 12/12, project-buttons + assistant checks 18/18, regression 30/30, auto tour pass (top auto-drive speed measured 84 km/h; target 85).

**Project buttons.** Items gained `live_url`, `repo_url`, `doc_url` (migration 002, applied automatically at server start; it moves any project row link you had already saved into the Live button). Rows with these are no longer links; each button opens only its own link and does not toggle the row. Items with no links and no details are plain rows.

**Assistant.** The old fallback printed raw text of the top matches. It is now a rule-based composer (contact, education, experience, research, project names with their own links, "does he know X" yes/no against all content). It is **not** an AI model and cannot reason beyond these rules; wrong or missing answers are still possible for unusual questions. 12 sample questions were checked, which is a small sample.

**Driving (measured by stepping the page's own `step()`, software GL):**

| | G-Wagon | Sports | Sedan |
|---|---|---|---|
| 0-100 km/h | 4.5 s | 3.2 s | 3.9 s |
| top speed | about 173 km/h | about 174 | about 174 |
| 100-0 km/h | 1.3 s | 1.3 s | 1.3 s |
| yaw at full lock, 20 / 50 / 85 km/h | 85 / 56 / 33 deg/s | same | same |

Steering uses a bicycle model with a 45 degree maximum wheel lock, reduced with speed and capped near 1.2 g cornering. The first attempt wrongly dropped top speed to 105 km/h and braked at about 5 g; both were caught by measurement and fixed. These numbers describe game units mapped at 4 km/h per unit, not a real vehicle.

**Sound.** The engine is now a three-oscillator V8-style rumble with a gear-dependent pitch sweep, a low-frequency burble, and a different profile per car. I verified only that it runs without errors (audio context running, sub oscillator and burble active). **I could not listen to it**, so how good it sounds is unverified.

**Car.** The G-Wagon is restyled (silver paint, glowing ring headlights, lit grille slats) from primitive shapes. It is a stylised low-poly model, not a licensed or scanned real model; your photo was used only as a style reference. Real models need a model file (.glb) you have the right to use.

**Known gaps:** project rows with buttons nest links inside a role=button row (screen-reader behavior untested); Sports and Sedan keep their old shapes; no mobile-device testing.


## Round 3 (2026-10-07): cockpit, sound, steering, coins

Results on the final build: API 16/16, admin end-to-end 12/12, features 18/18, cockpit/physics/sound 8/8, regression 30/30, strict auto tour pass (all 7 stops, top auto speed 84 km/h).

**Sound.** Engine output measured with an audio analyser, same drive on old and new code: old peak -6.6 dBFS / RMS -16.3 dBFS, new peak -12.4 dBFS / RMS -22.3 dBFS (about 6 dB quieter, peak about 0.24, no clipping in either). Changes: square wave replaced by triangle, filter resonance cut, a compressor/limiter and master gain added, and the engine "burble" modulation can no longer exceed the base level (it could previously push the gain negative, which flips the waveform). Crash sound reduced. **The measurement shows level, not how it sounds: I could not listen, so whether the distortion you heard is gone is unverified.**

**Cockpit.** Dashboard drawn on canvas in the style of your reference: hood in the car's paint colour, speedometer (km/h), fuel gauge, blinking turn arrows (follow the steering), hazard triangle, P/R/N/D. The fuel gauge and the N/hazard lights are cosmetic. Wheel: black three-spoke design, 540 degrees each way (assumed meaning of "one and a half rounds"; the constant is 540 in two places in tools/patch_v3.py), stops at the lock. Pedals: ribbed rubber brake (left) and gas (right).

**Physics visuals (checked numerically).** Front wheels yaw up to 45 degrees (negative yaw = right turn), all wheels spin at v*t/r (9.92 vs 10 expected), the body rolls so the outer side is lower, and the nose dips when braking.

**Coins.** 5 per road (35 with 7 sections), collected by driving through, with a counter and a chime.

**Not done.** (1) The map is still the roundabout-with-spokes layout; changing it affects collisions, the mini-map, signs, fast travel and the auto tour, so it needs its own phase and a decision on the layout you want. (2) The car is still a procedural model; a photoreal car needs a model file (.glb) you have the right to use, plus a loader. (3) Only the G-Wagon was restyled; the Sports and Sedan keep their old shapes.

**Test fixes made along the way:** the typewriter check was timing-sensitive and now samples over 6 seconds; the auto-tour check could double-click "Next" and skip a stop, so it now clicks once per stop and requires all 7 stops. A real bug was also found and fixed: steering past the lock kept counting, so reversing needed extra turns to unwind.
