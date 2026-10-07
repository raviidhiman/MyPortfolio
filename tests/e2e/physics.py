#!/usr/bin/env python3
"""Drives the page's own step() function in a tight loop (no rendering) to measure real physics numbers."""
import os, json
from playwright.sync_api import sync_playwright
THREE = open(os.path.join(os.path.dirname(__file__), "..", "vendor", "three-r128.min.js"), "rb").read()
BASE = os.environ.get("E2E_URL", "http://127.0.0.1:3100")
JS = """(carIdx)=>{
 const out={};carI=carIdx;
 const reset=(vv)=>{for(const k in K)K[k]=0;v=vv;const a=A[0];px=Math.cos(a)*70;pz=Math.sin(a)*70;H=Math.atan2(Math.cos(a),Math.sin(a));STR=0;AU.on=false};
 // 0-100 km/h (v=25) and top speed on a straight, 25 s
 reset(0);K.KeyW=1;let t=0,t100=null,t60=null,vm=0;while(t<25){step(1/60);t+=1/60;const kmh=Math.abs(v)*4;if(t60===null&&kmh>=60)t60=t;if(t100===null&&kmh>=100)t100=t;vm=Math.max(vm,kmh);if(Math.hypot(px,pz)>150){px=Math.cos(A[0])*70;pz=Math.sin(A[0])*70}}
 out.t0_60=t60&&+t60.toFixed(2);out.t0_100=t100&&+t100.toFixed(2);out.top_kmh=Math.round(vm);
 // braking 100 -> 0 with S key
 reset(25);K.KeyS=1;t=0;while(Math.abs(v)>.3&&t<10){step(1/60);t+=1/60}out.brake_100_to_0_s=+t.toFixed(2);
 // yaw rate (deg/s) at 20, 50, 85 km/h with full right lock held (D)
 out.yaw_deg_s={};for(const kmh of [20,50,85]){reset(kmh/4);K.KeyD=1;for(let i=0;i<30;i++){v=kmh/4;step(1/60)}const h0=H;v=kmh/4;for(let i=0;i<30;i++){v=kmh/4;step(1/60)}out.yaw_deg_s[kmh]=+(Math.abs(H-h0)*180/Math.PI*2).toFixed(1)}
 out.max_wheel_lock_deg=+(.7854*180/Math.PI).toFixed(0);out.car=CARS[carIdx].n;return out}"""
res = []
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]); c = b.new_context(viewport={"width": 640, "height": 360}); c.route("**/cdnjs.cloudflare.com/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=THREE))
    p = c.new_page(); p.goto(BASE + "/"); p.wait_for_timeout(800); p.click("#bDrive"); p.wait_for_timeout(4000); p.click("#cMan"); p.wait_for_timeout(300)
    p.evaluate("run=false;cancelAnimationFrame(raf)")   # freeze the live loop so only our calls step the sim
    for i in range(3): r = p.evaluate(JS, i); res.append(r); print(json.dumps(r))
    b.close()
json.dump(res, open(os.path.join(os.path.dirname(__file__), "physics-results.json"), "w"), indent=1)
