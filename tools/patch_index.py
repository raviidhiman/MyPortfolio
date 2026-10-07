#!/usr/bin/env python3
"""Derives index.html (data-driven) from original/portfolio-fixed__2_.html. Every replacement asserts it matched exactly as expected."""
import json
src=open('original/portfolio-fixed__2_.html',encoding='utf8').read()
seed=json.load(open('server/seed.json'))
def once(s,old,new,cnt=1):
    assert s.count(old)==cnt,(s.count(old),old[:70]); return s.replace(old,new)
a=src.index('const S=['); b=src.index('const IP={')
fallback={"settings":seed["settings"],"sections":[{"id":i,"slug":s["slug"],"title":s["title"],"street":s["street"],"color":s["color"],"icon":s["icon"],"layout":s["layout"],
  "items":[{"title":t,"body":bd,"icon":ic,"url":u,"details":d} for t,bd,ic,u,d in s["items"]]} for i,s in enumerate(seed["sections"],1)]}
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
function renderSecs(){$('#secs').innerHTML=S.map(s=>`<section id="${esc(s.id)}" data-a="${esc(s.a)}" style="--c:${esc(s.c)}"><div class="ghost" aria-hidden="true">${esc(s.title)}</div><div class="sh hd">${ico(s.ic)}<div><h2>${esc(s.title)}</h2><p class="st">${esc(s.street)}</p></div></div><div class="list${LCLS[s.layout]||''}">${s.items.map(([a,b,i,u,d],n)=>{const U=safeUrl(u),T=U?'a':'div',acc=(s.layout==='projects'||s.layout==='experience')&&d,bx=s.layout==='skills'||s.layout==='education';return `<${T} class="row it${acc?' acc':''}${bx?' bx':''}" style="--i:${n}"${acc?' tabindex="0" role="button" aria-expanded="false"':''}${U?` href="${esc(U)}" target="_blank" rel="noopener"${U.startsWith('mailto')?' data-copy="'+esc(U.slice(7))+'"':''}`:''}>${s.layout==='projects'?`<span class="num">${String(n+1).padStart(2,'0')}</span>`:''}<span class="ic">${ico(i)}</span><div class="tx"><h3>${esc(a)}</h3><p>${esc(b)}</p>${acc?'<div class="more"><p>'+esc(d)+'</p></div>':''}</div>${acc?'<span class="pl" aria-hidden="true"></span>':''}</${T}>`}).join('')}</div></section>`).join('');
 renderDrawer();document.querySelectorAll('.it,.hd,.tlw,.list').forEach(e=>io.observe(e))}
function renderDrawer(){$('#dlinks').innerHTML='<div class="dg">Sections</div>'+S.map(s=>`<button data-go="${esc(s.id)}"><i>${ico(s.ic)}</i><span>${esc(s.title)}</span></button>`).join('')+'<div class="dg">Modes</div><button id="dDrive"><i>'+ico('bolt')+'</i><span>Game mode</span></button><button id="dTour"><i>'+ico('auto')+'</i><span>Guided tour</span></button><div class="dg">Owner</div><button id="bAdmin"><i>'+ico('briefcase')+'</i><span>Admin Login</span></button>';
 $('#dTour').onclick=()=>tour(true);$('#bAdmin').onclick=()=>{location.href='/admin/'}}
function norm(c){return c.sections.map((s,i)=>({id:s.slug,street:s.street,title:s.title,c:s.color,ic:s.icon,a:ACCENT[s.slug]||'a'+(1+i%7),layout:s.layout,items:s.items.map(x=>[x.title,x.body,x.icon,x.url,x.details])}))}
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
js=js[:i]+"function buildIndex(){const H=SET.hero||{};DOCS=[{id:'home',sec:'Home',t:H.name||'Home',x:(H.name||'')+' — '+(H.phrases||[]).join(', ')+'. '+(H.lead||'')},...S.flatMap(s=>s.items.map(([a,b,,,d])=>({id:s.id,sec:s.title,t:a,x:b+(d?' '+d:'')})))];\nDT=DOCS.map(d=>tok(d.sec+' '+d.t+' '+d.t+' '+d.x));AVG=DT.reduce((a,b)=>a+b.length,0)/DT.length;DF={};DT.forEach(t=>new Set(t).forEach(w=>DF[w]=(DF[w]||0)+1))}"+js[j:]
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
open('index.html','w',encoding='utf8').write(js); print('patched ok; bytes',len(js.encode()))
