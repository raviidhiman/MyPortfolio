#!/usr/bin/env python3
"""Cockpit, wheel (540 deg), wheel/body physics, coins, and engine loudness old-vs-new. Needs dev server (tools/dev.sh) and `git show <old>:index.html > /tmp/old.html` for the sound comparison."""
import os, sys, json, math
from playwright.sync_api import sync_playwright
BASE = os.environ.get("E2E_URL", "http://127.0.0.1:3100"); OLD = os.environ.get("OLD_HTML", "/tmp/old.html")
HERE = os.path.dirname(__file__); THREE = open(os.path.join(HERE, "..", "vendor", "three-r128.min.js"), "rb").read()
res = []
def rec(i, n, ok, note=""): res.append({"id": i, "name": n, "result": "PASS" if ok else "FAIL", "note": note}); print(("PASS " if ok else "FAIL ") + i, n, "::", note, flush=True)
def mk(b, w=1280, h=720, old=False):
    c = b.new_context(viewport={"width": w, "height": h}); c.route("**/cdnjs.cloudflare.com/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=THREE))
    p = c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    if old: p.route(BASE + "/", lambda r: r.fulfill(status=200, content_type="text/html", body=open(OLD, encoding="utf8").read()))
    p.goto(BASE + "/"); p.wait_for_timeout(900); p.click("#bDrive")
    for _ in range(80):
        if p.evaluate("typeof THREE!=='undefined' && document.getElementById('drive').classList.contains('on')"): break
        p.wait_for_timeout(250)
    p.wait_for_timeout(1200); p.click("#cMan"); p.wait_for_timeout(300); return c, p, errs
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
    c, p, errs = mk(b)
    rec("C1", "cockpit camera is the default and the dashboard layer is on", p.evaluate("document.getElementById('drive').classList.contains('ck')") and p.evaluate("document.getElementById('dg').width>100"))
    p.keyboard.down("KeyW"); p.wait_for_timeout(2500); p.keyboard.down("KeyD"); p.wait_for_timeout(500); p.screenshot(path=os.path.join(HERE, "cockpit.png")); p.keyboard.up("KeyD"); p.keyboard.up("KeyW")
    # engine loudness (new)
    def loud(page, tap):
        page.evaluate("window.__an=AC.createAnalyser();window.__an.fftSize=2048;" + tap + ".connect(window.__an);window.__pk=0;window.__ss=0;window.__n=0")
        page.keyboard.down("KeyW"); page.wait_for_timeout(3000)
        for _ in range(40):
            page.evaluate("(()=>{const d=new Float32Array(2048);__an.getFloatTimeDomainData(d);for(const s of d){__pk=Math.max(__pk,Math.abs(s));__ss+=s*s;__n++}})()"); page.wait_for_timeout(60)
        page.keyboard.up("KeyW"); r = page.evaluate("[__pk, Math.sqrt(__ss/__n)]"); return r
    new = loud(p, "EN.out"); p.screenshot(path=os.path.join(HERE, "cockpit-after.png"))
    # deterministic physics checks (freeze the live loop)
    p.evaluate("run=false;cancelAnimationFrame(raf)")
    J = """(()=>{const out={};const reset=()=>{for(const k in K)K[k]=0;const a=A[0];px=Math.cos(a)*70;pz=Math.sin(a)*70;H=Math.atan2(Math.cos(a),Math.sin(a));STR=0;AU.on=false;WD=0;PV=0;RL=0;PT=0};
     reset();v=14;K.KeyD=1;for(let i=0;i<90;i++){v=14;step(1/60)}car.updateMatrixWorld(true);const left=car.localToWorld(new THREE.Vector3(1,1,0)).y,right=car.localToWorld(new THREE.Vector3(-1,1,0)).y;
     out.right_turn={STR:+STR.toFixed(2),roll:+car.rotation.z.toFixed(4),left_side_y:+left.toFixed(3),right_side_y:+right.toFixed(3),front_wheel_yaw_deg:+(car.userData.fw[0].rotation.y*57.3).toFixed(1)};
     reset();const s0=car.userData.sp[0].rotation.x;v=10;K.KeyD=0;for(let i=0;i<30;i++){v=10;step(1/60)}out.wheel_spin_rad_in_0_5s=+(car.userData.sp[0].rotation.x-s0).toFixed(2);out.expected_spin=+(10*.5/CARS[carI].r).toFixed(2);
     reset();v=22;K.KeyS=1;for(let i=0;i<25;i++)step(1/60);car.updateMatrixWorld(true);const fr=car.localToWorld(new THREE.Vector3(0,1,CARS[carI].L/2)).y,rr=car.localToWorld(new THREE.Vector3(0,1,-CARS[carI].L/2)).y;out.braking={pitch:+car.rotation.x.toFixed(4),front_y:+fr.toFixed(3),rear_y:+rr.toFixed(3)};
     reset();return out})()"""
    r = p.evaluate(J); print(json.dumps(r))
    rt = r["right_turn"]
    rec("C2", "right turn: front wheels point right (negative yaw), body rolls so the outer (left) side is lower", rt["STR"] > .9 and rt["front_wheel_yaw_deg"] < -3 and rt["left_side_y"] < rt["right_side_y"], json.dumps(rt))
    rec("C3", "wheels spin by about v*t/r", abs(r["wheel_spin_rad_in_0_5s"] - r["expected_spin"]) < .3, f"{r['wheel_spin_rad_in_0_5s']} vs {r['expected_spin']}")
    br = r["braking"]; rec("C4", "hard braking dips the nose (front lower than rear)", br["front_y"] < br["rear_y"], json.dumps(br))
    # wheel drag: 1.5 rounds each way
    box = p.locator("#wheelw").bounding_box(); cx, cy_ = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2; R = min(box["width"], 100) * .3
    pos = lambda deg: (cx + R * math.cos(math.radians(deg)), cy_ + R * math.sin(math.radians(deg)))
    p.mouse.move(*pos(-90)); p.mouse.down(); out = {}
    for deg in range(-90, -90 + 541, 12): p.mouse.move(*pos(deg)); 
    p.evaluate("step(1/60)"); out["after_540"] = [p.evaluate("+STR.toFixed(2)"), p.evaluate("$('#wheel').style.transform")]
    for deg in range(450, 450 + 181, 12): p.mouse.move(*pos(deg))
    p.evaluate("step(1/60)"); out["after_extra_180"] = [p.evaluate("+STR.toFixed(2)"), p.evaluate("$('#wheel').style.transform")]
    for deg in range(630, 630 - 541 - 540, -12): p.mouse.move(*pos(deg))
    p.evaluate("step(1/60)"); out["after_reverse_1080"] = [p.evaluate("+STR.toFixed(2)"), p.evaluate("$('#wheel').style.transform")]
    p.mouse.up(); print(json.dumps(out))
    rec("C5", "wheel turns 1.5 rounds (540 deg) each way and stops at the lock", out["after_540"][0] == 1 and "540deg" in out["after_540"][1] and out["after_extra_180"][0] == 1 and out["after_reverse_1080"][0] == -1 and "-540deg" in out["after_reverse_1080"][1], json.dumps(out))
    # coins
    r2 = p.evaluate("(()=>{const n=COINS.length,c=COINS[0].m.position;px=c.x;pz=c.z;v=0;step(1/60);return [n,SCORE,$('#coins').textContent,COINS[0].m.visible]})()")
    rec("C6", "coins: 35 placed; driving into one collects it and updates the counter", r2[0] == 35 and r2[1] == 1 and "1 / 35" in r2[2] and r2[3] is False, str(r2))
    rec("C7", "no script errors in the new build", not errs, str(errs)); c.close()
    # engine loudness (old build, same procedure)
    c, p, e2 = mk(b, old=True); old = loud(p, "EG"); c.close()
    db = lambda x: round(20 * math.log10(max(x, 1e-9)), 1)
    rec("S1", "engine output: new build is quieter than the old and never clips", new[0] < old[0] and new[0] < .5, f"old peak={old[0]:.3f} ({db(old[0])} dBFS) rms={old[1]:.3f} ({db(old[1])} dBFS) | new peak={new[0]:.3f} ({db(new[0])} dBFS) rms={new[1]:.3f} ({db(new[1])} dBFS)")
    b.close()
json.dump(res, open(os.path.join(HERE, "cockpit-results.json"), "w"), indent=1)
print("TOTAL pass=%d fail=%d" % (sum(r["result"] == "PASS" for r in res), sum(r["result"] == "FAIL" for r in res)))
