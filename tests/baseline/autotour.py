#!/usr/bin/env python3
"""Runs ONLY the auto-tour baseline (slow under software GL) and writes autotour-result.json.
Usage: AUTOTOUR_BUDGET=900 python3 tests/baseline/autotour.py"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
import baseline as B
from playwright.sync_api import sync_playwright
B.results.clear()
srv = B.serve()
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    ctx = B.new_ctx(b, 480, 270); B.route_three(ctx); p = B.open_page(ctx)
    def run():
        p.click("#bDrive"); p.wait_for_function("window.THREE && document.getElementById('drive').classList.contains('on')", timeout=30000); p.wait_for_timeout(800)
        p.click("#cAuto"); seen = []; t0 = time.time(); done = False; budget = int(os.environ.get("AUTOTOUR_BUDGET", "240"))
        while time.time() - t0 < budget:
            p.wait_for_timeout(500)
            h = B.ev(p, "(document.querySelector('#panel h3')||{}).textContent||''")
            if h and (not seen or seen[-1] != h): seen.append(h.strip())
            if "Tour complete" in h: done = True; break
            if B.ev(p, "document.getElementById('panel').classList.contains('on') && !!document.getElementById('aNext')"): p.click("#aNext")
        if done: p.screenshot(path=os.path.join(B.SHOTS, "drive-30-tour-complete.png"))
        return (done, f"panels seen={seen} elapsed={time.time()-t0:.0f}s of {budget}s budget (software GL ~7fps => sim runs slower than real time)")
    B.check("D12", "auto tour reaches 'Tour complete' (Next clicked at each stop to skip waits)", run)
    b.close()
srv.shutdown()
json.dump(B.results, open(os.path.join(B.OUT, "autotour-result.json"), "w"), indent=1)
