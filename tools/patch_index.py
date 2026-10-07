#!/usr/bin/env python3
"""Derives index.html (data-driven) from original/portfolio-fixed__2_.html. Every replacement asserts it matched exactly as expected."""
import json
src=open('original/portfolio-fixed__2_.html',encoding='utf8').read()
seed=json.load(open('server/seed.json'))
def once(s,old,new,cnt=1):
    assert s.count(old)==cnt,(s.count(old),old[:70]); return s.replace(old,new)
a=src.index('const S=['); b=src.index('const IP={')
fallback={"settings":seed["settings"],"sections":[{"id":i,"slug":s["slug"],"title":s["title"],"street":s["street"],"color":s["color"],"icon":s["icon"],"layout":s["layout"],
  "items":[{"title":t,"body":bd,"icon":ic,"url":u,"details":d,"live_url":"","repo_url":"","doc_url":""} for t,bd,ic,u,d in s["items"]]} for i,s in enumerate(seed["sections"],1)]}
js=src[:a]+"const S=[];let SET={},A=[],secEls=[],dB=[];\nconst FALLBACK="+json.dumps(fallback,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+";\n"+src[b:]
js=once(js,'<b>${a}</b> — ${b}','<b>${esc(a)}</b> — ${esc(b)}')
js=once(js,'<b>${a}</b> &mdash; ${b}','<b>${esc(a)}</b> &mdash; ${esc(b)}')
js=js.replace('${s.title}','${esc(s.title)}'); js=js.replace('${s.street}','${esc(s.street)}')
js=once(js,'>${x.sec}</button>','>${esc(x.sec)}</button>')
js=once(js,"S[near].title+' &middot; details'","esc(S[near].title)+' &middot; details'")
lines=js.split('\n'); i0=next(i for i,l in enumerate(lines) if l.startswith("$('#secs').innerHTML="))
assert lines[i0+1].startswith("$('#dlinks').innerHTML=") and lines[i0+2].startswith('const io=') and lines[i0+3].startswith("document.querySelectorAll('.it,.hd,.tlw,.list')")
NEW=r"""const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=u=>/^(https?:\/\/[^\s]+|mailto:[^\s@]+@[^\s@]+)$/i.test(u||'')?u:'';
const io=new IntersectionObserver(e=>e.forEach(x=>x.isIntersecting&&x.target.classList.add('in')),{threshold:.15,rootMargin:'0px 0px -6% 0px'});
const LCLS={experience:' tlw',skills:' flexg skl',education:' flexg edg',contact:' con'},ACCENT={about:'a1',skills:'a2',projects:'a3',experience:'a4',education:'a5',research:'a7',contact:'a6'};
function renderSecs(){$('#secs').innerHTML=S.map(s=>`<section id="${esc(s.id)}" data-a="${esc(s.a)}" style="--c:${esc(s.c)}"><div class="ghost" aria-hidden="true">${esc(s.title)}</div><div class="sh hd">${ico(s.ic)}<div><h2>${esc(s.title)}</h2><p class="st">${esc(s.street)}</p></div></div><div class="list${LCLS[s.layout]||''}">${s.items.map(([a,b,i,u,d,lv,rp,dc],n)=>{const LK=[['Live',lv],['GitHub',rp],['Docs',dc]].filter(([,x])=>safeUrl(x)),acc=(s.layout==='projects'||s.layout==='experience')&&(d||LK.length),U=acc?'':safeUrl(u),T=U?'a':'div',bx=s.layout==='skills'||s.layout==='education';return `<${T} class="row it${acc?' acc':''}${bx?' bx':''}" style="--i:${n}"${acc?' tabindex="0" role="button" aria-expanded="false"':''}${U?` href="${esc(U)}" target="_blank" rel="noopener"${U.startsWith('mailto')?' data-copy="'+esc(U.slice(7))+'"':''}`:''}>${s.layout==='projects'?`<span class="num">${String(n+1).padStart(2,'0')}</span>`:''}<span class="ic">${ico(i)}</span><div class="tx"><h3>${esc(a)}</h3><p>${esc(b)}</p>${acc?'<div class="more">'+(d?'<p>'+esc(d)+'</p>':'')+(LK.length?'<div class="lk">'+LK.map(([n,x])=>`<a href="${esc(x)}" target="_blank" rel="noopener">${n}</a>`).join('')+'</div>':'')+'</div>':''}</div>${acc?'<span class="pl" aria-hidden="true"></span>':''}</${T}>`}).join('')}</div></section>`).join('');
 renderDrawer();document.querySelectorAll('.lk a').forEach(a=>['click','keydown'].forEach(ev=>a.addEventListener(ev,e=>e.stopPropagation())));document.querySelectorAll('.it,.hd,.tlw,.list').forEach(e=>io.observe(e))}
function renderDrawer(){$('#dlinks').innerHTML='<div class="dg">Sections</div>'+S.map(s=>`<button data-go="${esc(s.id)}"><i>${ico(s.ic)}</i><span>${esc(s.title)}</span></button>`).join('')+'<div class="dg">Modes</div><button id="dDrive"><i>'+ico('bolt')+'</i><span>Game mode</span></button><button id="dTour"><i>'+ico('auto')+'</i><span>Guided tour</span></button><div class="dg">Owner</div><button id="bAdmin"><i>'+ico('briefcase')+'</i><span>Admin Login</span></button>';
 $('#dTour').onclick=()=>tour(true);$('#bAdmin').onclick=()=>{location.href='/admin/'}}
function norm(c){return c.sections.map((s,i)=>({id:s.slug,street:s.street,title:s.title,c:s.color,ic:s.icon,a:ACCENT[s.slug]||'a'+(1+i%7),layout:s.layout,items:s.items.map(x=>[x.title,x.body,x.icon,x.url,x.details,x.live_url,x.repo_url,x.doc_url])}))}
let PENDING=null;
renderDrawer();
function applyContent(c){if(typeof run!=='undefined'&&run){PENDING=c;return}
 S.length=0;norm(c).forEach(s=>S.push(s));SET=c.settings||{};const H=SET.hero||{};
 if(typeof ready!=='undefined'&&ready){try{ren.dispose()}catch(_){}ready=false;FT.length=0}
 A=S.map((_,i)=>i*2*Math.PI/S.length);renderSecs();
 if(SET.site){document.title=SET.site.title;const m=document.querySelector('meta[name=description]');if(m)m.content=SET.site.description||''}
 const t=document.querySelector('.hero .tag');if(t)t.textContent=H.tag||'';document.querySelector('h1').textContent=H.name||'';document.querySelector('.hero .lead').textContent=H.lead||'';
 $('#bDrive').firstChild.textContent=(H.cta||'Enter game mode to explore')+' ';
 RO.length=0;(H.phrases||[]).forEach(p=>RO.push(p));ri=0;ci=0;dl=0;if(reduce)$('#ty').textContent=RO.join(' · ');
 $('#soc').innerHTML=(SET.socials||[]).filter(x=>safeUrl(x.url)).map(x=>`<a href="${esc(x.url)}" target="_blank" rel="noopener" aria-label="${esc(x.label)}">${ico(x.icon)}</a>`).join('');
 $('#exp').innerHTML=S.map(s=>`<button data-go="${esc(s.id)}">${ico(s.ic)}${esc(s.title)}</button>`).join('');
 secEls=[...document.querySelectorAll('#secs section')];
 $('#dots').innerHTML=[['home','Home'],...S.map(s=>[s.id,s.title])].map(([id,t])=>`<button data-go="${esc(id)}" data-t="${esc(t)}" aria-label="${esc(t)}"></button>`).join('');
 dB=[...document.querySelectorAll('#dots button')];buildIndex();spy()}"""
lines[i0:i0+4]=NEW.split('\n'); js='\n'.join(lines)
i=js.index('const DOCS=['); j=js.index('\n',i); js=js[:i]+"let DOCS,DT,AVG,DF;"+js[j:]
i=js.index('const DT=DOCS.map'); j=js.index('\n',i)
js=js[:i]+"function buildIndex(){const H=SET.hero||{};DOCS=[{id:'home',sec:'Home',t:H.name||'Home',x:(H.name||'')+' — '+(H.phrases||[]).join(', ')+'. '+(H.lead||'')},...S.flatMap(s=>s.items.map(([a,b,,,d,lv,rp,dc])=>({id:s.id,sec:s.title,t:a,x:b+(d?' '+d:'')+(lv?' live demo website':'')+(rp?' github repository code':'')+(dc?' documentation document':'')})))];\nDT=DOCS.map(d=>tok(d.sec+' '+d.t+' '+d.t+' '+d.x));AVG=DT.reduce((a,b)=>a+b.length,0)/DT.length;DF={};DT.forEach(t=>new Set(t).forEach(w=>DF[w]=(DF[w]||0)+1))}"+js[j:]
js=once(js,"$('#bAdmin').onclick=()=>{closeAll();$('#modal').classList.add('on')};$('#xModal').onclick=closeAll;","$('#xModal').onclick=closeAll;")
js=once(js,"const RO=['AI & ML solutions','data dashboards','full-stack web apps'];","const RO=FALLBACK.settings.hero.phrases.slice();")
for pre in ["const SOCH=","$('#exp').innerHTML=S.map","const secEls=","$('#dots').innerHTML=","const dB="]:
    i=js.index('\n'+pre)+1; j=js.index('\n',i); js=js[:i]+js[j+1:]
js=once(js,",A=S.map((_,i)=>i*2*Math.PI/S.length),COL=[]",",COL=[]")
js=once(js,"document.body.style.overflow=document.documentElement.style.overflow='';$('#panel').classList.remove('on');}","document.body.style.overflow=document.documentElement.style.overflow='';$('#panel').classList.remove('on');if(PENDING){const c=PENDING;PENDING=null;applyContent(c)}}")
js=once(js,"$('#mm').onclick=()=>$('#fast').classList.toggle('on');\n</script>","""$('#mm').onclick=()=>$('#fast').classList.toggle('on');
applyContent(FALLBACK);
fetch('/api/public/content',{headers:{accept:'application/json'}}).then(r=>r.ok?r.json():Promise.reject()).then(c=>{if(c&&Array.isArray(c.sections)&&c.sections.length)applyContent(c)}).catch(()=>{});
</script>""")

# ===== v2: buttons css, answer composer, driving, sound, car =====
CSS=".lk{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.lk a{font-size:12px;letter-spacing:.3px;padding:4px 13px;border:1px solid var(--c);border-radius:999px;color:var(--c);text-decoration:none;background:transparent;transition:background .2s}.lk a:hover,.lk a:focus-visible{background:color-mix(in srgb,var(--c) 20%,transparent)}\n"
js=once(js,'</style>',CSS+'</style>')
COMPOSE=r"""const GEN=new Set('doe wa know knows ravi dhiman skill tech stack tool language familiar experience expert good work use used have proficient programming technology technologies'.split(' '));
function compose(q,hits){const ql=q.toLowerCase(),T=id=>(S.find(s=>s.id===id)||{items:[]}).items,jn=a=>a.join('; '),
 lk=x=>[['Live',x[5]],['GitHub',x[6]],['Docs',x[7]]].filter(([,u])=>safeUrl(u)).map(([n,u])=>n+': '+u).join(' · ');
 const top=hits[0],qt=tok(q),GP=['market','marketplace','analytics','analysis','prediction','pipeline','freelance','project','risk'];
 const pm=T('projects').find(x=>tok(x[0]).some(w=>w.length>4&&!GP.includes(w)&&qt.includes(w)));
 if(pm){const W=[[/github|repo|source|code/,'GitHub',6],[/live|demo|deployed|website|visit|link/,'Live',5],[/\bdocs?\b|document|report|pdf/,'Docs',7]].find(([r])=>r.test(ql));
  if(W){const u=pm[W[2]];return safeUrl(u)?pm[0]+' — '+W[1]+': '+u:'No '+W[1]+' link has been added for '+pm[0]+' yet.'}
  const l=lk(pm);return pm[0]+' — '+pm[1]+(pm[4]?' '+pm[4]:'')+(l?' ('+l+')':' (no links are added for this project yet)')}
 const soc=['github','linkedin','instagram'].find(k=>ql.includes(k));if(soc&&!/project|repo|code of/.test(ql)){const it=T('contact').find(x=>x[0].toLowerCase()===soc);if(it)return "Ravi's "+it[0]+': '+it[3]}
 if(/e-?mail|contact|reach|get in touch|hire|phone/.test(ql)){const c=T('contact');if(c.length)return 'You can reach Ravi here — '+jn(c.map(x=>x[0]+': '+x[1]))+'.'}
 if(/educat|degree|stud(y|ied)|college|universit|cgpa|qualif|school|\bmca\b|\bbca\b|marks|percentage/.test(ql)){const e=T('education');if(e.length)return jn(e.map(x=>x[0]+' ('+x[1]+')'))+'.'}
 if(/intern|experience|worked|working|company|companies|job|role/.test(ql)&&!/skill|tech/.test(ql)){const e=T('experience');if(e.length)return jn(e.map(x=>x[0]+' — '+x[1]))+'.'}
 if(/research|paper|publi|journal|dissertation|thesis/.test(ql)){const r=T('research');if(r.length)return jn(r.map(x=>x[0]+(x[1]?' — '+x[1]:'')+(safeUrl(x[3])?' ('+x[3]+')':'')))}
 if(/\bprojects?\b|built|made|portfolio of|worked on/.test(ql)&&!/skill|tech/.test(ql)){const p=T('projects');if(p.length)return 'Ravi\'s projects: '+jn(p.map(x=>x[0]))+'. Ask about any one of them for details and links.'}
 if(/skill|tech|stack|language|tools?\b|know|familiar|expert|good at|proficien|use\b|uses\b|knowledge/.test(ql)){
  const terms=tok(q).filter(w=>!GEN.has(w)&&!/^(skill|tech|stack|tool|language)$/.test(w));
  for(const w of terms){const f=S.flatMap(s=>s.items.map(x=>({s,x}))).find(({x})=>(x[0]+' '+x[1]+' '+(x[4]||'')).toLowerCase().includes(w));if(f)return 'Yes — '+w+' appears in the '+f.s.title+' section ('+f.x[0]+').'}
  if(terms.length&&!/skills|what|which|list/.test(ql))return "I don't see "+terms.join(', ')+' listed on the portfolio.';
  const sk=T('skills');if(sk.length)return "Ravi's skills — "+jn(sk.map(x=>x[0]+': '+x[1]))+'.'}
 if(/who|about|introduc|yourself|tell me about|ravi/.test(ql)){const a=T('about');if(a.length)return a.map(x=>x[1]).join(' ')}
 if(!top)return "I couldn't find that on the portfolio yet. Try asking about skills, projects, experience, education or contact.";
 const sn=top.x.length>260?top.x.slice(0,257)+'…':top.x;return top.t+': '+sn+' (see the '+top.sec+' section)'}
let askId=0;"""
js=once(js,"let askId=0;",COMPOSE)
js=once(js,"if(!hits.length){at.className='at';at.textContent=","if(!hits.length){at.className='at';at.textContent=compose(q,hits)||")
js=once(js,r"""const fb=()=>hits.slice(0,3).map(x=>`${x.t} — ${x.x}`).join('\n'),done=""","const fb=()=>compose(q,hits),done=")
# --- driving ---
js=once(js,"const CARS=[","const CPW=[6.5,9,7.5];const CARS=[")
js=once(js,"if(gas)v+=30*dt;","if(gas)v+=(v<0?30:CPW[carI]*(1-Math.pow(Math.min(1,v/44),2))+.5*Math.min(v,44))*dt;")
js=once(js,"H-=STR*1.9*dt*Math.max(-1,Math.min(1,v/8));","{const yr=Math.tan(STR*.7854/(1+Math.pow(v/16,2)))*(v/(CARS[carI].L*.6)),lim=12/Math.max(Math.abs(v),1);H-=Math.max(-lim,Math.min(lim,yr))*dt}")
js=once(js,"if(br){if(AU.on)v=Math.max(0,v-45*dt);else v>.5?v-=45*dt:v-=18*dt}if(sp)v-=Math.sign(v)*Math.min(Math.abs(v),50*dt);","if(br){if(AU.on)v=Math.max(0,v-30*dt);else v>.5?v-=14*dt:v-=18*dt}if(sp)v-=Math.sign(v)*Math.min(Math.abs(v),24*dt);")
js=once(js,"(AU.k<AU.slow?7:15)","(AU.k<AU.slow?7:21.25)")
# --- sound ---
import re as _re
def repl_line(js,start,new):
    i=js.index(start); j=js.index('\n',i); return js[:i]+new+js[j:]
js=repl_line(js,"function audioInit(){","function audioInit(){if(AC)return;try{AC=new (window.AudioContext||window.webkitAudioContext)();const o1=AC.createOscillator(),o2=AC.createOscillator(),o3=AC.createOscillator(),lf=AC.createOscillator(),lg=AC.createGain(),f=AC.createBiquadFilter(),f2=AC.createBiquadFilter();o1.type='sawtooth';o2.type='square';o3.type='sawtooth';lf.type='sine';f.type='lowpass';f.frequency.value=420;f.Q.value=2;f2.type='peaking';f2.frequency.value=90;f2.gain.value=9;EG=AC.createGain();EG.gain.value=0;lg.gain.value=0;lf.connect(lg);lg.connect(EG.gain);o1.connect(f);o2.connect(f);o3.connect(f);f.connect(f2);f2.connect(EG);EG.connect(AC.destination);[o1,o2,o3,lf].forEach(o=>o.start());EN={o1,o2,o3,lf,lg,f}}catch(e){AC=null}}")
js=repl_line(js,"function audioUpd(","function audioUpd(g,sp){if(!AC||!EN)return;const P=[{k:.78,b:.022,c:.8},{k:1.3,b:.008,c:1.5},{k:1,b:.004,c:1}][carI]||{k:1,b:.01,c:1},gear=1+Math.min(5,sp/8|0),rpm=(sp%8)/8,fq=(30+rpm*44+gear*6+(g?14:0))*P.k,t=AC.currentTime;EN.o1.frequency.setTargetAtTime(fq,t,.05);EN.o2.frequency.setTargetAtTime(fq*.5,t,.05);EN.o3.frequency.setTargetAtTime(fq*.25,t,.05);EN.lf.frequency.setTargetAtTime(fq/2.1,t,.05);EN.lg.gain.setTargetAtTime(P.b*(g?1.4:.7),t,.1);EN.f.frequency.setTargetAtTime((260+sp*12+(g?260:0))*P.c,t,.08);EG.gain.setTargetAtTime(SND?(.04+(g?.06:0)+Math.min(.04,sp*.0011)):0,t,.08)}")
# --- G-Wagon look: silver paint, glowing ring headlights, lit grille ---
js=once(js,"{n:'G-Wagon',g:1,c:0x14161a,","{n:'G-Wagon',g:1,c:0xb9bdc4,")
js=once(js,"car.add(sp)}","car.add(sp);[-.65,.65].forEach(x=>{const r=new THREE.Mesh(new THREE.TorusGeometry(.27,.035,8,28),new THREE.MeshBasicMaterial({color:0xe9f6ff}));r.position.set(x,1.0,d.L/2+.14);car.add(r)});[0,1,2,3,4].forEach(k=>{const m=new THREE.Mesh(new THREE.BoxGeometry(1.0,.03,.03),new THREE.MeshBasicMaterial({color:0xcfe3f5}));m.position.set(0,.8+k*.08,d.L/2+.17);car.add(m)})}")

import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import patch_v3
js=patch_v3.apply(js,once,repl_line)
open('index.html','w',encoding='utf8').write(js); print('patched ok; bytes',len(js.encode()))
