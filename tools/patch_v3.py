"""v3 changes applied on top of patch_index.py: cockpit dashboard, 1.5-round wheel, pedals, wheel/body physics, coins, softer sound."""
import re

CSS2 = """#tr{left:0!important;right:0!important;bottom:0!important;height:0;pointer-events:none}
.tc .ped{position:absolute!important;pointer-events:auto;border-radius:12px!important;border:1px solid #000!important;color:#9aa0aa!important;font-size:10px!important;letter-spacing:2px;background:repeating-linear-gradient(0deg,#2b2e34 0 6px,#17191d 6px 10px)!important;box-shadow:0 5px 0 #08080a,0 10px 16px #000b;transition:transform .06s,box-shadow .06s}
.tc .ped[data-k=b]{left:3%!important;bottom:calc(24px + env(safe-area-inset-bottom,0px))!important;width:min(120px,16vw)!important;height:min(60px,15vh)!important}
.tc .ped[data-k=g]{right:3%!important;bottom:calc(24px + env(safe-area-inset-bottom,0px))!important;width:min(64px,9vw)!important;height:min(108px,26vh)!important}
.tc .ped:active{transform:translateY(4px);box-shadow:0 1px 0 #08080a,0 3px 8px #000b;background:repeating-linear-gradient(0deg,#3a3e46 0 6px,#23262b 6px 10px)!important;color:#fff!important}
#wheelw{left:57%!important;bottom:-7vh!important;width:min(250px,40vh)!important;height:min(250px,40vh)!important}
#dash{height:38vh!important;min-height:190px!important}
#coins{margin-left:8px;color:#ffd24a}
"""

WHEEL_SVG = '''<svg id="wheel" viewBox="0 0 100 100"><defs><linearGradient id="wlt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#555a64"/><stop offset=".5" stop-color="#1b1d22"/><stop offset="1" stop-color="#0a0b0d"/></linearGradient><radialGradient id="whb" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#eceef2"/><stop offset=".6" stop-color="#8c929c"/><stop offset="1" stop-color="#3a3e45"/></radialGradient></defs><circle cx="50" cy="50" r="43" fill="none" stroke="#050506" stroke-width="14"/><circle cx="50" cy="50" r="43" fill="none" stroke="url(#wlt)" stroke-width="11"/><circle cx="50" cy="50" r="46.4" fill="none" stroke="#ffffff26" stroke-width=".7"/><g fill="#17191d" stroke="#000" stroke-width=".7"><path d="M44 51 L7 58 L7 64 L46 62Z"/><path d="M56 51 L93 58 L93 64 L54 62Z"/><path d="M45 58 L44 91 L56 91 L55 58Z"/></g><circle cx="50" cy="50" r="12.5" fill="url(#whb)" stroke="#000" stroke-width="1.2"/><circle cx="50" cy="50" r="7.8" fill="none" stroke="#2b2e34" stroke-width="1"/><rect x="47.3" y="2.5" width="5.4" height="9" rx="2.2" fill="#e23b3b"/></svg>'''

DASH = r"""function dash(){const c=$('#dg'),x=c.getContext('2d'),W=c.width,Hh=c.height;if(!W)return;x.clearRect(0,0,W,Hh);
const col='#'+CARS[carI].c.toString(16).padStart(6,'0'),sp=Math.abs(v)*4,t=performance.now(),cy=Hh*.7,r=Math.min(Hh*.25,80);
x.fillStyle=col;x.beginPath();x.moveTo(0,Hh*.5);x.quadraticCurveTo(W/2,Hh*.16,W,Hh*.5);x.lineTo(W,Hh);x.lineTo(0,Hh);x.fill();
let g=x.createLinearGradient(0,Hh*.18,0,Hh*.52);g.addColorStop(0,'#ffffff55');g.addColorStop(1,'#00000066');x.fillStyle=g;x.fill();
g=x.createLinearGradient(0,Hh*.5,0,Hh);g.addColorStop(0,'#1f2126');g.addColorStop(1,'#07080a');x.fillStyle=g;x.fillRect(0,Hh*.5,W,Hh*.5);x.fillStyle='#ffffff1c';x.fillRect(0,Hh*.5,W,2);
dial(x,W*.3,cy,r,sp,200,Math.round(sp)+'');x.fillStyle='#8d96c4';x.font='11px Arial';x.textAlign='center';x.fillText('km/h',W*.3,cy+r*.86);
const fr=r*.68,fx=W*.47;x.save();x.translate(fx,cy);x.fillStyle='#0b0c0f';x.beginPath();x.arc(0,0,fr,0,7);x.fill();x.strokeStyle='#cfd3da';x.lineWidth=2;x.stroke();const fa=(200+.7*140)*Math.PI/180;x.strokeStyle='#ff5a36';x.lineWidth=3;x.beginPath();x.moveTo(0,0);x.lineTo(Math.cos(fa)*fr*.8,Math.sin(fa)*fr*.8);x.stroke();x.fillStyle='#cfd3da';x.font='bold '+Math.round(fr*.26)+'px Arial';x.textAlign='center';x.fillText('E',-fr*.58,fr*.22);x.fillText('F',fr*.58,fr*.22);x.restore();
const bl=((t/380)|0)%2,ar=(cx,cyy,d,on)=>{x.fillStyle=on?'#37e06b':'#16301f';x.beginPath();x.moveTo(cx+d*11,cyy);x.lineTo(cx-d*6,cyy-9);x.lineTo(cx-d*6,cyy+9);x.closePath();x.fill()};
ar(W*.385,cy+r*.15,-1,STR<-.2&&bl);ar(W*.425,cy+r*.15,1,STR>.2&&bl);
x.strokeStyle='#b52b2b';x.lineWidth=3;x.beginPath();x.moveTo(W*.405,cy-r*.55);x.lineTo(W*.405+12,cy-r*.55+20);x.lineTo(W*.405-12,cy-r*.55+20);x.closePath();x.stroke();
const gs=v<-.25?'R':Math.abs(v)<.25?'P':'D';x.font='bold 15px Arial';x.textAlign='center';['P','R','N','D'].forEach((q,k)=>{x.fillStyle=q===gs?'#37e06b':'#5a5f69';x.fillText(q,W*.8,Hh*.6+k*Hh*.1)})}"""

OLD_WHEELS = "[[1,1],[-1,1],[1,-1],[-1,-1]].forEach(([sx,sz])=>{const g=new THREE.Group();g.add(new THREE.Mesh(new THREE.CylinderGeometry(d.r,d.r,.3,18),tm),new THREE.Mesh(new THREE.CylinderGeometry(d.r*.68,d.r*.68,.32,12),rm));g.rotation.z=Math.PI/2;g.position.set(sx*(d.W/2-.12),d.r,sz*d.L*.3);car.add(g)});"
NEW_WHEELS = "car.userData={fw:[],sp:[]};[[1,1],[-1,1],[1,-1],[-1,-1]].forEach(([sx,sz])=>{const P=new THREE.Group(),Sp=new THREE.Group(),g=new THREE.Group();g.add(new THREE.Mesh(new THREE.CylinderGeometry(d.r,d.r,.3,24),tm),new THREE.Mesh(new THREE.CylinderGeometry(d.r*.68,d.r*.68,.32,20),rm));g.rotation.z=Math.PI/2;Sp.add(g);for(let k=0;k<3;k++){const sk=new THREE.Mesh(new THREE.BoxGeometry(.34,d.r*.11,d.r*1.3),tm);sk.rotation.x=k*Math.PI/3;Sp.add(sk)}P.position.set(sx*(d.W/2-.12),d.r,sz*d.L*.3);P.add(Sp);car.add(P);car.userData.sp.push(Sp);if(sz>0)car.userData.fw.push(P)});"

BODY = "car.position.set(px,0,pz);car.rotation.y=H;{const U=car.userData,sa=STR*.7854/(1+Math.pow(v/16,2)),tr=-STR*Math.min(1,Math.abs(v)/18)*.05,pt=Math.max(-.04,Math.min(.04,-(v-PV)/Math.max(dt,.001)*.0035));PV=v;RL+=(tr-RL)*Math.min(1,6*dt);PT+=(pt-PT)*Math.min(1,6*dt);car.rotation.z=RL;car.rotation.x=PT;if(U.fw){U.fw.forEach(q=>q.rotation.y=-sa);U.sp.forEach(q=>q.rotation.x+=v*dt/CARS[carI].r)}}"

COINS = r"""const COINS=[];let SCORE=0;
function makeCoins(){COINS.forEach(c=>sc.remove(c.m));COINS.length=0;COINS.sc=sc;SCORE=0;const gm=new THREE.CylinderGeometry(.42,.42,.1,24),mt=new THREE.MeshBasicMaterial({color:0xffd24a}),rg=new THREE.TorusGeometry(.42,.07,8,24),rt=new THREE.MeshBasicMaterial({color:0xb8860b}),ig=new THREE.CylinderGeometry(.22,.22,.12,16),it=new THREE.MeshBasicMaterial({color:0xfff0a8});S.forEach((s,i)=>{for(let k=0;k<5;k++){const d=R0+16+k*((E-R0-30)/4),o=(k%2?-1:1)*3.2,a=A[i],m=new THREE.Group(),dk=new THREE.Mesh(gm,mt);dk.rotation.x=Math.PI/2;m.add(dk);const rm2=new THREE.Mesh(rg,rt),im=new THREE.Mesh(ig,it);im.rotation.x=Math.PI/2;m.add(rm2,im);m.position.set(Math.cos(a)*d-Math.sin(a)*o,1.3,Math.sin(a)*d+Math.cos(a)*o);sc.add(m);COINS.push({m,on:1})}});updCoins()}
function updCoins(){const e=$('#coins');if(e)e.textContent='★ '+SCORE+' / '+COINS.length}
function ping(){if(!AC||!SND)return;const t=AC.currentTime,o=AC.createOscillator(),g=AC.createGain();o.type='sine';o.frequency.setValueAtTime(880,t);o.frequency.exponentialRampToValueAtTime(1500,t+.09);g.gain.setValueAtTime(.05,t);g.gain.exponentialRampToValueAtTime(.001,t+.16);o.connect(g);g.connect(AC.destination);o.start(t);o.stop(t+.18)}
function coinTick(dt){for(const c of COINS){if(!c.on)continue;c.m.rotation.y+=dt*3;if(Math.hypot(px-c.m.position.x,pz-c.m.position.z)<2.4){c.on=0;c.m.visible=false;SCORE++;updCoins();ping();if(SCORE===COINS.length)$('#street').textContent='All coins collected!'}}}
function step(dt){coinTick(dt);"""

AUDIO_INIT = "function audioInit(){if(AC)return;try{AC=new (window.AudioContext||window.webkitAudioContext)();const o1=AC.createOscillator(),o2=AC.createOscillator(),o3=AC.createOscillator(),lf=AC.createOscillator(),lg=AC.createGain(),f=AC.createBiquadFilter(),f2=AC.createBiquadFilter(),cp=AC.createDynamicsCompressor(),mg=AC.createGain();o1.type='sawtooth';o2.type='triangle';o3.type='sine';lf.type='sine';f.type='lowpass';f.frequency.value=380;f.Q.value=.7;f2.type='peaking';f2.frequency.value=80;f2.gain.value=5;EG=AC.createGain();EG.gain.value=0;lg.gain.value=0;lf.connect(lg);lg.connect(EG.gain);o1.connect(f);o2.connect(f);o3.connect(f);f.connect(f2);f2.connect(EG);cp.threshold.value=-24;cp.knee.value=18;cp.ratio.value=8;cp.attack.value=.005;cp.release.value=.2;mg.gain.value=.55;EG.connect(cp);cp.connect(mg);mg.connect(AC.destination);[o1,o2,o3,lf].forEach(o=>o.start());EN={o1,o2,o3,lf,lg,f,out:mg}}catch(e){AC=null}}"
AUDIO_UPD = "function audioUpd(g,sp){if(!AC||!EN)return;const P=[{k:.78,b:.008,c:.8},{k:1.3,b:.003,c:1.5},{k:1,b:.0015,c:1}][carI]||{k:1,b:.003,c:1},gear=1+Math.min(5,sp/8|0),rpm=(sp%8)/8,fq=(30+rpm*44+gear*6+(g?14:0))*P.k,t=AC.currentTime;EN.o1.frequency.setTargetAtTime(fq,t,.05);EN.o2.frequency.setTargetAtTime(fq*.5,t,.05);EN.o3.frequency.setTargetAtTime(fq*.25,t,.05);EN.lf.frequency.setTargetAtTime(fq/2.1,t,.05);EN.lg.gain.setTargetAtTime(P.b*(g?1.3:.7),t,.1);EN.f.frequency.setTargetAtTime((240+sp*9+(g?160:0))*P.c,t,.1);EG.gain.setTargetAtTime(SND?(.02+(g?.035:0)+Math.min(.02,sp*.0007)):0,t,.1)}"


def apply(js, once, repl_line):
    js = once(js, '</style>', CSS2 + '</style>')
    js, n = re.subn(r'<svg id="wheel".*?</svg>', lambda m: WHEEL_SVG, js, count=1, flags=re.S); assert n == 1
    js = once(js, '<span class="pill" id="street">—</span>', '<span class="pill" id="street">—</span><span class="pill" id="coins">★ 0 / 0</span>')
    js = once(js, "let STR=0,WD=0,WV=0,a0=0,w0=0;", "let STR=0,WD=0,WV=0,a0=0,w0=0,wa=0,la=0;")
    js = once(js, "WV=STR;a0=ang(e);w0=STR*100;", "WV=STR;a0=ang(e);w0=STR*540;wa=0;la=a0;")
    js = once(js, "let d=ang(e)-a0;if(d>180)d-=360;if(d<-180)d+=360;WV=Math.max(-1,Math.min(1,(w0+d)/100))", "const aN=ang(e);let d=aN-la;if(d>180)d-=360;if(d<-180)d+=360;wa=Math.max(-540-w0,Math.min(540-w0,wa+d));la=aN;WV=Math.max(-1,Math.min(1,(w0+wa)/540))")
    js = once(js, "'rotate('+STR*100+'deg)'", "'rotate('+STR*540+'deg)'")
    i = js.index("function dash(){"); END = "mid,Hh*.93)}"; j = js.index(END, i) + len(END)
    js = js[:i] + DASH + js[j:]
    js = once(js, "resize();goTo(i);audioInit();", "resize();while(cm!==3)camNext();sizeDash();goTo(i);audioInit();")
    js = once(js, "try{if(!ready)init();}", "try{if(!ready)init();if(COINS.sc!==sc)makeCoins();}")
    js = once(js, "car=new THREE.Group();", "car=new THREE.Group();car.rotation.order='YXZ';")
    js = once(js, OLD_WHEELS, NEW_WHEELS)
    js = once(js, "const CPW=[6.5,9,7.5];", "const CPW=[6.5,9,7.5];let PV=0,RL=0,PT=0;")
    js = once(js, "car.position.set(px,0,pz);car.rotation.y=H;", BODY)
    js = once(js, "function step(dt){", COINS)
    js = repl_line(js, "function audioInit(){", AUDIO_INIT)
    js = repl_line(js, "function audioUpd(", AUDIO_UPD)
    js = once(js, "Math.min(.9,.25+p*.03)", "Math.min(.35,.1+p*.012)")
    js = once(js, "og.gain.setValueAtTime(.5,t)", "og.gain.setValueAtTime(.22,t)")
    return js
