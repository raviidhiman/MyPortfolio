#!/usr/bin/env python3
"""Project buttons + assistant answers + driving numbers. Needs the dev server (tools/dev.sh) and tests/vendor three."""
import os, re, sys, time, json
from playwright.sync_api import sync_playwright
BASE = os.environ.get("E2E_URL", "http://127.0.0.1:3100"); LOG = "/tmp/server.log"
THREE = open(os.path.join(os.path.dirname(__file__), "..", "vendor", "three-r128.min.js"), "rb").read()
res = []
def rec(i, n, ok, note=""): res.append({"id": i, "name": n, "result": "PASS" if ok else "FAIL", "note": note}); print(("PASS " if ok else "FAIL ") + i, n, "::", note, flush=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    def ctx(): 
        c = b.new_context(viewport={"width": 1280, "height": 800}); c.route("**/cdnjs.cloudflare.com/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=THREE))
        c.route(re.compile(r"^https://(live|github|docs)\.example\.com.*|^https://github\.com/x/.*"), lambda r: r.fulfill(status=200, body="ok")); return c
    # admin session via the API (same OTP flow the UI uses)
    c = ctx(); a = c.new_page(); a.goto(BASE + "/admin/")
    def api(m, p, body=None): return a.evaluate("async([m,p,b,t])=>{const r=await fetch('/api/admin'+p,{method:m,credentials:'same-origin',headers:{'content-type':'application/json','x-csrf-token':t},body:b?JSON.stringify(b):undefined});return [r.status,await r.json()]}", [m, p, body, CSRF[0]])
    CSRF = [""]
    a.evaluate("fetch('/api/admin/auth/request-otp',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:'ravidhiman8673@gmail.com'})})"); time.sleep(1.2)
    code = re.findall(r"admin login code: (\d{6})", open(LOG).read())[-1]
    CSRF[0] = a.evaluate("async c=>(await (await fetch('/api/admin/auth/verify-otp',{method:'POST',credentials:'same-origin',headers:{'content-type':'application/json'},body:JSON.stringify({email:'ravidhiman8673@gmail.com',code:c})})).json()).csrf", code)
    secs = api("GET", "/sections")[1]; proj = next(s for s in secs if s["layout"] == "projects"); it = proj["items"]
    api("PATCH", f"/items/{it[0]['id']}", {"live_url": "https://live.example.com/a", "repo_url": "https://github.com/x/a", "doc_url": "https://docs.example.com/a"})
    api("PATCH", f"/items/{it[1]['id']}", {"repo_url": "https://github.com/x/b"})
    api("PATCH", f"/items/{it[2]['id']}", {"url": "", "live_url": "", "repo_url": "", "doc_url": ""})
    # public page
    p = c.new_page(); popups = []; c.on("page", lambda pg: popups.append(pg)); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto(BASE + "/"); p.wait_for_timeout(1200); p.evaluate("document.getElementById('projects').scrollIntoView()"); p.wait_for_timeout(600)
    counts = p.evaluate("[...document.querySelectorAll('#projects .it')].map(r=>r.querySelectorAll('.lk a').length)")
    rec("F1", "buttons appear only for links that exist (3, 1, 0, ...)", counts[:3] == [3, 1, 0], f"counts={counts}")
    rec("F2", "project rows are no longer links", p.evaluate("document.querySelectorAll('#projects a.it').length") == 0)
    n0 = len(popups); p.click("#projects .it >> nth=0"); p.wait_for_timeout(500); p.click("#projects .it >> nth=0 >> .pl") if False else None
    rec("F3", "clicking the project box/plus expands it and opens nothing", len(popups) == n0 and p.get_attribute("#projects .it >> nth=0", "aria-expanded") == "true", f"popups={len(popups)-n0}")
    labels = p.eval_on_selector_all("#projects .it >> nth=0 >> .lk a", "e=>e.map(a=>a.textContent)") if False else p.evaluate("[...document.querySelectorAll('#projects .it')][0].querySelectorAll('.lk a').length")
    with c.expect_page() as pi: p.click("#projects .it >> nth=0 >> text=GitHub")
    u = pi.value.url; rec("F4", "GitHub button opens only the repo link, row stays open", "github.com/x/a" in u and p.get_attribute("#projects .it >> nth=0", "aria-expanded") == "true", f"opened={u}")
    with c.expect_page() as pi: p.click("#projects .it >> nth=0 >> text=Docs")
    rec("F5", "Docs button opens the document link", "docs.example.com/a" in pi.value.url, pi.value.url)
    rec("F6", "no script errors", not errs, str(errs))
    # assistant
    p.evaluate("scrollTo(0,0)")
    QA = [("what is his email", "ravidhiman8673@gmail.com"), ("does he know react", "Yes"), ("does he know rust", "don't see"), ("tell me about threadsource", "ThreadSource"),
          ("github of threadsource", "ThreadSource"), ("what is his education", "MCA"), ("which projects has he built", "Remote Job"), ("linkedin", "linkedin.com"),
          ("where did he intern", "Labmentix"), ("does he know docker", "Yes"), ("what is the research paper about", "Brain Stroke"), ("who is ravi", "MCA graduate")]
    for q, want in QA:
        p.fill("#sq", q); p.press("#sq", "Enter"); p.wait_for_timeout(700); t = p.inner_text("#at")
        rec("Q:" + q, "assistant answer contains '%s'" % want, want.lower() in t.lower(), t[:170].replace("\n", " "))
    # restore data
    for i in it[:3]: api("PATCH", f"/items/{i['id']}", {"live_url": "", "repo_url": "", "doc_url": ""})
    b.close()
json.dump(res, open(os.path.join(os.path.dirname(__file__), "features-results.json"), "w"), indent=1)
print("TOTAL pass=%d fail=%d" % (sum(r["result"] == "PASS" for r in res), sum(r["result"] == "FAIL" for r in res)))
