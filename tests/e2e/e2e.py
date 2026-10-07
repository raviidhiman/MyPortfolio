#!/usr/bin/env python3
"""End-to-end: real server + real PostgreSQL + headless Chromium. Usage: E2E_URL=http://127.0.0.1:3100 E2E_LOG=server.log python3 tests/e2e/e2e.py"""
import os, re, sys, json, time
from playwright.sync_api import sync_playwright
BASE = os.environ.get("E2E_URL", "http://127.0.0.1:3100"); LOG = os.environ.get("E2E_LOG", "/tmp/server.log")
THREE = open(os.path.join(os.path.dirname(__file__), "..", "vendor", "three-r128.min.js"), "rb").read()
res = []
def rec(i, n, ok, note=""): res.append({"id": i, "name": n, "result": "PASS" if ok else "FAIL", "note": note}); print(("PASS " if ok else "FAIL ") + i, n, "::", note, flush=True)
def check(i, n, f):
    try: r = f(); rec(i, n, *(r if isinstance(r, tuple) else (bool(r), "")))
    except Exception as e: rec(i, n, False, "exception: " + str(e).split("\n")[0][:220])
def ctx(b, **kw):
    c = b.new_context(viewport={"width": 1280, "height": 800}, **kw); c.route("**/cdnjs.cloudflare.com/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=THREE)); return c
def wait_drive(p, secs=25):
    for _ in range(secs * 4):
        if p.evaluate("typeof THREE!=='undefined' && document.getElementById('drive').classList.contains('on')"): return
        p.wait_for_timeout(250)
    raise TimeoutError("Drive Mode did not start")
def last_code():
    for _ in range(30):
        m = re.findall(r"admin login code: (\d{6})", open(LOG).read())
        if m: return m[-1]
        time.sleep(.3)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    # public site from API
    c = ctx(b); errs = []; p = c.new_page(); p.on("pageerror", lambda e: errs.append(str(e))); p.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    p.goto(BASE + "/"); p.wait_for_timeout(1200)
    body = p.inner_text("body")
    check("E1", "public page renders 7 sections from the API with profile content, no placeholders, no errors",
          lambda: (p.eval_on_selector_all("#secs section", "e=>e.length") == 7 and "Labmentix" in body and "Placeholder" not in body and "CONFIRM" not in body.upper().replace("CONFIRMATION","") and not errs, f"errors={errs}"))
    check("E2", "hero, socials and links come from settings", lambda: (p.inner_text("h1") == "Ravi Dhiman" and p.eval_on_selector_all("#soc a", "e=>e.map(a=>a.href)") == ["mailto:ravidhiman8673@gmail.com", "https://github.com/raviidhiman", "https://www.linkedin.com/in/raviidhiman", "https://www.instagram.com/ravii.dhiman/"], ""))
    check("E3", "accordion project rows open and show details", lambda: (p.click("#projects .acc >> nth=0") or p.wait_for_timeout(300) or True) and "Python, n8n" in p.inner_text("#projects"))
    c.close()
    # admin flow through the UI
    c = ctx(b); a = c.new_page(); a.on("dialog", lambda d: d.accept()); a.goto(BASE + "/admin/")
    def signin():
        a.click("text=Send code"); a.wait_for_selector("input[maxlength='6']", state="visible"); code = last_code(); a.fill("input[maxlength='6']", code); a.click("text=Verify and sign in")
        a.wait_for_selector("text=Sign out", timeout=8000); return True
    check("E4", "admin signs in via emailed one-time code (dev log); session cookie is HttpOnly", lambda: (signin() and all(ck["httpOnly"] for ck in c.cookies() if ck["name"] == "sid") and len([ck for ck in c.cookies() if ck["name"] == "sid"]) == 1, ""))
    def add_section():
        a.click("button.tab:has-text('Sections')"); a.click("text=+ Add section"); lab = a.locator(".card input").first; lab.fill("Awards")
        a.locator(".card input").nth(1).fill("Awards Alley"); a.locator("button.btn.pri:text-is('Add section')").click(); a.wait_for_selector("b:has-text('Awards')"); return True
    check("E5", "admin adds a new section (Sections tab)", add_section)
    def add_item():
        a.click("button.tab:has-text('Content')"); a.select_option("select >> nth=0", label="Awards"); a.click("text=+ Add item to Awards")
        a.locator(".card input").first.fill("<img src=x onerror=window.__x=1> Best Project"); a.locator(".card textarea").first.fill("Body & <b>text</b>"); a.locator("button.btn.pri:text-is('Add')").click(); a.wait_for_selector("b:has-text('Best Project')"); return True
    check("E6", "admin adds an item (including hostile HTML)", add_item)
    c2 = ctx(b); pp = c2.new_page(); perr = []; pp.on("pageerror", lambda e: perr.append(str(e))); pp.goto(BASE + "/"); pp.wait_for_timeout(1200)
    check("E7", "public site shows the new section (8 total) and renders hostile text inertly", lambda: (pp.eval_on_selector_all("#secs section", "e=>e.length") == 8 and pp.evaluate("window.__x") is None and "Best Project" in pp.inner_text("#secs") and pp.eval_on_selector_all("#secs img", "e=>e.length") == 0, f"errors={perr}"))
    def drive8():
        pp.click("#bDrive"); wait_drive(pp); pp.wait_for_timeout(1500)
        n = pp.evaluate("[S.length, document.querySelectorAll('#fast button').length, A.length]"); pp.click("#cMan"); pp.keyboard.down("KeyW"); pp.wait_for_timeout(1500); pp.keyboard.up("KeyW")
        sp = pp.evaluate("Math.round(Math.abs(v)*4)"); pp.click("#bFast"); pp.click("[data-ft='7']"); pp.wait_for_timeout(500)
        st = pp.inner_text("#street"); pp.screenshot(path=os.path.join(os.path.dirname(__file__), "drive-8-sections.png")); return (n == [8, 8, 8] and sp > 3 and st == "Awards Alley" and not perr, f"S/fast/A={n} speed={sp} street='{st}' errors={perr}")
    check("E8", "Drive Mode builds 8 roads for 8 sections, drives, fast-travels to the new street", drive8)
    c2.close()
    def delete_section():
        a.click("button.tab:has-text('Sections')"); row = a.locator(".row:has(b:has-text('Awards'))"); row.locator("button:has-text('Delete')").click(); a.wait_for_timeout(800); return a.locator("b:has-text('Awards')").count() == 0
    check("E9", "admin deletes the section (with confirmation)", delete_section)
    c3 = ctx(b); p3 = c3.new_page(); p3.goto(BASE + "/"); p3.wait_for_timeout(1000)
    check("E10", "public site is back to 7 sections", lambda: p3.eval_on_selector_all("#secs section", "e=>e.length") == 7); c3.close()
    def signout():
        a.click("text=Sign out"); a.wait_for_selector("text=Admin sign in"); return a.evaluate("fetch('/api/admin/sections').then(r=>r.status)") if False else True
    check("E11", "sign out returns to login", signout)
    st = a.evaluate("fetch('/api/admin/sections',{credentials:'same-origin'}).then(r=>r.status)"); rec("E12", "after sign-out the admin API returns 401", st == 401, f"status={st}")
    b.close()
json.dump(res, open(os.path.join(os.path.dirname(__file__), "e2e-results.json"), "w"), indent=1)
print("TOTAL pass=%d fail=%d" % (sum(r["result"] == "PASS" for r in res), sum(r["result"] == "FAIL" for r in res)))
