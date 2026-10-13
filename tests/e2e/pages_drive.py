#!/usr/bin/env python3
"""Browser test: section pages + Back, burger menu, Reach-out toggle, Connect page, and the new Drive controls
(brake, drift, P-R-N-D gears, gear-knob hiding, pedals, open section page from the game and Back to Drive).
Run against the real server: E2E_URL=http://127.0.0.1:3100 python3 tests/e2e/pages_drive.py"""
import os, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(__file__); BASE = os.environ.get("E2E_URL", "http://127.0.0.1:3100")
THREE = open(os.path.join(HERE, "..", "vendor", "three-r128.min.js"), "rb").read()
SHOTS = os.path.join(HERE, "shots"); os.makedirs(SHOTS, exist_ok=True); res = []
def check(name, ok, note=""):
    res.append({"name": name, "pass": bool(ok), "note": str(note)}); print(("PASS " if ok else "FAIL ") + name, "::", note, flush=True)
def ctx(b, **kw):
    c = b.new_context(**kw); c.route("**/cdnjs.cloudflare.com/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=THREE)); return c
def wait_on(p, id_, ms=90000):
    for _ in range(ms // 500):
        if p.evaluate(f"!!document.getElementById('{id_}')&&document.getElementById('{id_}').classList.contains('on')"): return
        p.wait_for_timeout(500)
    raise TimeoutError(id_)
def start_drive(p):
    p.goto(BASE + "/"); p.wait_for_timeout(1000); p.click("#bDrive"); wait_on(p, "choose"); p.click("#cMan", timeout=60000); p.wait_for_timeout(400)
FREEZE = "run=false;cancelAnimationFrame(raf)"
RESET = "(vv,g)=>{for(const k in K)K[k]=0;TC.g=0;TC.b=0;v=vv;uL=0;STR=0;grip=40;slipA=0;AU.on=0;GEAR=g;gearUI();gHide=0;GE.classList.remove('hide')}"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    # ---------- pages (desktop + phone) ----------
    for name, vp, touch in [("desktop", {"width": 1280, "height": 800}, False), ("phone", {"width": 390, "height": 780}, True)]:
        c = ctx(b, viewport=vp, has_touch=touch, is_mobile=touch); p = c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
        p.goto(BASE + "/"); p.wait_for_timeout(1200)
        check(f"{name}: landing still scrolls all 7 sections on one page", p.evaluate("document.querySelectorAll('#secs section').length") == 7)
        check(f"{name}: Reach-out toggle sits in the Contact section", p.evaluate("!!document.querySelector('#contact .tgl')"))
        p.click("#bHam"); p.wait_for_timeout(400)
        items = p.evaluate("[...document.querySelectorAll('#dlinks button')].map(b=>b.textContent.trim())")
        check(f"{name}: burger menu lists every section + 'Connect / Reach out'", items[:8] == ["About", "Skills", "Projects", "Experience", "Education", "Research", "Contact", "Connect / Reach out"], items)
        with p.expect_navigation(): p.click("#dlinks button[data-page='/skills']")
        p.wait_for_timeout(1200)
        check(f"{name}: burger link opens its own page /skills", p.url.endswith("/skills") and p.evaluate("[...document.querySelectorAll('#secs section')].map(s=>s.id)") == ["skills"])
        check(f"{name}: page has its own title, no hero, Back button", p.title() == "Skills — Ravi Dhiman" and p.evaluate("getComputedStyle(document.querySelector('.hero')).display") == "none" and p.is_visible("#pbBack"))
        p.screenshot(path=f"{SHOTS}/{name}-section-page.png")
        with p.expect_navigation(): p.click("#pbBack")
        check(f"{name}: Back returns to the previous page", p.url.rstrip("/") == BASE.rstrip("/"))
        p.evaluate("document.querySelector('#contact .tgl').scrollIntoView({block:'center'})"); p.wait_for_timeout(500)
        with p.expect_navigation(): p.click("#contact .tgl")
        check(f"{name}: toggle opens /connect", p.url.endswith("/connect") and p.is_visible("#cf-form"))
        p.wait_for_timeout(800); p.screenshot(path=f"{SHOTS}/{name}-connect.png")
        check(f"{name}: no page errors", not errs, errs); c.close()
    # ---------- drive controls ----------
    c = ctx(b, viewport={"width": 1280, "height": 720}); p = c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    start_drive(p); p.screenshot(path=f"{SHOTS}/drive-controls.png"); p.evaluate(FREEZE)
    check("sedan and car-change button are gone", p.evaluate("!document.getElementById('bCar')&&CARS.length===1&&CARS[0].n==='G-Class'"))
    check("no DRIFT button; brake + gas pedals and the P R N D selector exist", p.evaluate("!document.querySelector('[data-k=h]')&&!!document.getElementById('pBrake')&&!!document.getElementById('pGas')&&document.querySelectorAll('#gear .gl').length===4"))
    for key in ["KeyS", "Space"]:
        r = p.evaluate(f"(rs)=>{{({RESET})(25,'D');K.{key}=1;let mn=1e9;for(let i=0;i<600;i++){{step(1/60);mn=Math.min(mn,v)}}return {{mn,v}}}}", None)
        check(f"brake ({key}) stops the car and never reverses it", r["mn"] >= 0 and r["v"] == 0, r)
    g = lambda gear: p.evaluate(f"(()=>{{({RESET})(0,'{gear}');K.KeyW=1;for(let i=0;i<180;i++)step(1/60);return v}})()")
    d, rr, n, pk = g("D"), g("R"), g("N"), g("P")
    check("gas: D drives forward, R drives backward, N and P do not move the car", d > 15 and rr < -10 and abs(n) < .01 and abs(pk) < .01, [round(d, 1), round(rr, 1), n, pk])
    r = p.evaluate(f"(()=>{{({RESET})(20,'D');return [setGear('R'),setGear('P'),GEAR,setGear('N'),GEAR]}})()")
    check("at 72 km/h R and P are refused (toast), N is allowed", r == [False, False, "D", True, "N"], r)
    check("stopped: R is accepted", p.evaluate(f"(()=>{{({RESET})(0,'D');return [setGear('R'),GEAR]}})()") == [True, "R"])
    h = p.evaluate(f"(()=>{{({RESET})(0,'D');const o=[];for(const k of [30,22,18,24]){{v=k/3.6;step(1/600);o.push(GE.classList.contains('hide'))}}return o}})()")
    check("gear knob hides above 25 km/h, stays hidden at 22, returns below 20, stays at 24 after returning", h == [True, True, False, False], h)
    dr = p.evaluate(f"(()=>{{({RESET})(25,'D');K.Space=1;K.KeyD=1;let g=40,s=0;for(let i=0;i<90;i++){{step(1/60);g=Math.min(g,grip);s=Math.max(s,slipA)}}return {{g,s}}}})()")
    st = p.evaluate(f"(()=>{{({RESET})(25,'D');K.Space=1;let g=40;for(let i=0;i<90;i++){{step(1/60);g=Math.min(g,grip)}}return g}})()")
    sn = p.evaluate(f"(()=>{{({RESET})(25,'D');K.KeyD=1;let g=40;for(let i=0;i<90;i++){{step(1/60);g=Math.min(g,grip)}}return g}})()")
    check("brake + steering at speed drifts; braking straight or steering alone does not", dr["g"] <= 2 and dr["s"] > .8 and st == 40 and sn == 40, [dr, st, sn])
    check("no page errors in Drive Mode", not errs, errs); c.close()
    # ---------- from the game to a section page and back ----------
    c = ctx(b, viewport={"width": 1100, "height": 700}); p = c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    start_drive(p); p.evaluate(FREEZE); p.evaluate("goTo(1)")
    p.evaluate("(()=>{for(const k in K)K[k]=0;K.KeyW=1;let n=0;while(opened<0&&n<2000){step(1/60);n++}K.KeyW=0;K.Space=1;for(let i=0;i<200;i++)step(1/60);K.Space=0})()")
    p.evaluate("run=true;last=performance.now();loop(last)"); p.wait_for_timeout(600); p.click("#dinfo"); p.wait_for_timeout(400)
    before = p.evaluate("({px,pz,H})"); label = p.inner_text("#pn")
    p.click("#pn", no_wait_after=True); p.wait_for_url("**/skills", timeout=90000); p.wait_for_timeout(1500)
    check("'Open full page' opens that section's own page (not the landing page)", label == "Open full page" and p.url.endswith("/skills") and p.evaluate("[...document.querySelectorAll('#secs section')].map(s=>s.id)") == ["skills"], p.url)
    check("page shows Back to Drive", p.is_visible("#pbDrive")); p.screenshot(path=f"{SHOTS}/page-from-game.png")
    p.click("#pbDrive"); p.wait_for_timeout(2000); wait_on(p, "drive")
    for _ in range(180):
        if p.evaluate("typeof run!=='undefined'&&run===true"): break
        p.wait_for_timeout(500)
    p.wait_for_timeout(500)
    after = p.evaluate("({run,px,pz,H,key:sessionStorage.getItem('rd_drive')})")
    check("Back to Drive resumes the game at the exact spot where it was left", after["run"] and abs(after["px"] - before["px"]) < .01 and abs(after["pz"] - before["pz"]) < .01 and abs(after["H"] - before["H"]) < .01 and after["key"] is None, [before, after])
    p.screenshot(path=f"{SHOTS}/resumed.png"); check("no page errors on the round trip", not errs, errs); c.close(); b.close()
json.dump(res, open(os.path.join(HERE, "pages-drive-results.json"), "w"), indent=1)
print("\n%d/%d passed" % (sum(r["pass"] for r in res), len(res)))
