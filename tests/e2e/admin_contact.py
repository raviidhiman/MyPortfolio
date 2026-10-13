#!/usr/bin/env python3
"""Browser test: Admin Login page, 30 s resend, contact form -> Messages -> chat invite -> live chat -> close.
Needs the dev server (login codes and e-mails are printed to its log): E2E_URL=http://127.0.0.1:3100 E2E_LOG=/tmp/server.log"""
import os, re, json, time
from playwright.sync_api import sync_playwright
BASE = os.environ.get("E2E_URL", "http://127.0.0.1:3100"); LOG = os.environ.get("E2E_LOG", "/tmp/server.log")
SHOTS = os.path.join(os.path.dirname(__file__), "shots"); os.makedirs(SHOTS, exist_ok=True)
res = []
def check(name, ok, note=""):
    res.append({"name": name, "pass": bool(ok), "note": note}); print(("PASS " if ok else "FAIL ") + name, "::", note, flush=True)
def last(pattern):
    t = open(LOG).read(); m = re.findall(pattern, t); return m[-1] if m else None
with sync_playwright() as pw:
    b = pw.chromium.launch()
    # ---------- admin login page ----------
    c = b.new_context(viewport={"width": 1000, "height": 700}); p = c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto(BASE + "/admin/"); p.wait_for_timeout(600)
    texts = p.evaluate("[...document.body.querySelectorAll('*')].filter(e=>e.children.length===0&&e.textContent.trim()&&e.offsetParent!==null&&!['SCRIPT','STYLE'].includes(e.tagName)).map(e=>e.textContent.trim())")
    check("login: only 'Admin Login' + 'Send code' are visible text", texts == ["Admin Login", "Send code"], str(texts))
    check("login: no email field", p.evaluate("document.querySelectorAll('input[type=email],input[name=email]').length") == 0)
    box = p.evaluate("(()=>{const r=document.querySelector('.login').getBoundingClientRect();const h=document.querySelector('.login h1').getBoundingClientRect();const b=document.querySelector('.login .big').getBoundingClientRect();return {cx:(r.left+r.right)/2,cy:(r.top+r.bottom)/2,hx:(h.left+h.right)/2,bx:(b.left+b.right)/2,gy:(h.top+b.bottom)/2,vh:innerHeight}})()")
    check("login: heading and button are centered on the page", abs(box["hx"] - 500) < 2 and abs(box["bx"] - 500) < 2 and abs(box["gy"] - box["vh"] / 2) < 30, str(box))
    check("login: back-to-site arrow (icon only) links to /", p.evaluate("(()=>{const a=document.querySelector('a.goback');return a&&a.getAttribute('href')==='/'&&a.textContent.trim()===''&&!!a.querySelector('svg')})()"))
    check("login: favicon is the 192 icon", p.evaluate("[...document.querySelectorAll('link[rel*=icon]')].map(l=>l.getAttribute('href'))") == ["/assets/icons/android-chrome-192x192.png"])
    p.screenshot(path=SHOTS + "/admin-login.png")
    t0 = time.time(); p.click("text=Send code"); p.wait_for_selector(".codein", state="visible", timeout=5000)
    check("login: code box appears after Send code; Send button gone", p.evaluate("document.querySelector('.big').hidden===true||document.querySelector('.big').offsetParent===null"))
    rb = p.locator(".step2 .ghost"); check("login: Resend is disabled with a countdown", rb.is_disabled() and "Resend in" in rb.inner_text(), rb.inner_text())
    p.screenshot(path=SHOTS + "/admin-login-code.png")
    code1 = last(r"admin login code: (\d{6})"); check("login: code was 'e-mailed' (dev log) to ADMIN_EMAIL", bool(code1))
    p.wait_for_timeout(max(0, 31.2 - (time.time() - t0)) * 1000)
    check("login: Resend unlocks after 30 s", rb.is_enabled() and rb.inner_text() == "Resend code", rb.inner_text())
    rb.click(); p.wait_for_timeout(1200); code2 = last(r"admin login code: (\d{6})")
    check("login: Resend sends a new code and restarts the countdown", code2 and code2 != code1 and rb.is_disabled(), f"{code1}->{code2}")
    p.fill(".codein", "000000"); p.click("text=Verify"); p.wait_for_timeout(800)
    check("login: wrong code rejected", p.locator(".codein").is_visible() and "Invalid" in p.inner_text("body"))
    p.fill(".codein", code2); p.click("text=Verify"); p.wait_for_selector("text=Messages", timeout=5000)
    check("login: valid code opens the admin panel (Messages tab present)", True)
    # ---------- visitor contact form ----------
    v = b.new_context(viewport={"width": 420, "height": 800}); vp = v.new_page(); vp.goto(BASE + "/connect"); vp.wait_for_timeout(1200)
    check("connect: WhatsApp button points at +91 93065 39506", (vp.get_attribute(".wa", "href") or "").startswith("https://wa.me/919306539506"))
    vp.fill("input[name=name]", "Asha Verma"); vp.fill("input[name=email]", "asha@example.com"); vp.fill("textarea[name=message]", "Hello Ravi, I would love to talk about a project.")
    vp.screenshot(path=SHOTS + "/connect-filled.png"); vp.click("button.go"); vp.wait_for_selector(".cdone", timeout=5000)
    check("connect: form submits and shows the thank-you card", True); vp.screenshot(path=SHOTS + "/connect-done.png")
    mail = open(LOG).read(); check("connect: owner is e-mailed the form (dev log shows it)", "New message from Asha Verma" in mail)
    # ---------- admin Messages + invite ----------
    p.click("text=Messages"); p.wait_for_selector("text=Asha Verma", timeout=5000); p.screenshot(path=SHOTS + "/admin-messages.png")
    p.click("text=Asha Verma"); p.wait_for_selector("text=Send chat invite"); p.screenshot(path=SHOTS + "/admin-message-detail.png")
    p.click("text=Send chat invite"); p.wait_for_selector("text=Chat", timeout=5000); p.wait_for_timeout(500)
    link = last(r"(http://[^\s]+/chat/[A-Za-z0-9_-]+)"); check("invite: visitor receives a private chat link by e-mail", bool(link), str(link))
    # ---------- visitor chat ----------
    vp.goto(link); vp.wait_for_selector("#f:not([hidden])", timeout=5000)
    check("chat: visitor page opens, greets by name, status Open", "Asha" in vp.inner_text("#who") and vp.inner_text("#st") == "Open")
    vp.fill("#m", "Hi Ravi, are you free this week?"); vp.click("#b"); vp.wait_for_selector(".bub.visitor", timeout=5000)
    p.wait_for_selector(".chatlog .bub.visitor", timeout=8000); check("chat: admin sees the visitor message live (polling)", True)
    p.fill(".composer textarea", "Hi Asha! Yes, Thursday works."); p.click(".composer >> text=Send"); vp.wait_for_selector(".bub.admin", timeout=8000)
    check("chat: visitor sees the admin reply live", "Thursday" in vp.inner_text("#log")); vp.screenshot(path=SHOTS + "/chat-visitor.png"); p.screenshot(path=SHOTS + "/admin-chat.png")
    p.once("dialog", lambda d: d.accept()); p.click("text=Close chat"); p.wait_for_timeout(800)
    check("chat: admin closes it; composer is gone for the admin", p.locator(".composer").is_hidden())
    vp.wait_for_selector("#closedNote", timeout=8000); check("chat: visitor sees 'closed' and can no longer type", vp.locator("#f").is_hidden() and vp.inner_text("#st") == "Closed")
    vp.screenshot(path=SHOTS + "/chat-closed.png")
    bad = vp.evaluate("fetch(location.pathname.replace('/chat/','/api/chat/')+'/post',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({body:'x'})}).then(r=>r.status)")
    check("chat: server refuses posts on a closed chat (409)", bad == 409, str(bad))
    check("no page errors in admin", not errs, str(errs)); b.close()
json.dump(res, open(os.path.join(os.path.dirname(__file__), "admin-contact-results.json"), "w"), indent=1)
print("\n%d/%d passed" % (sum(r["pass"] for r in res), len(res)))
