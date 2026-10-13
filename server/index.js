'use strict';
const express = require('express'), cookieParser = require('cookie-parser'), crypto = require('crypto'), compression = require('compression'), rag = require('./rag');
const fs = require('fs'), path = require('path'), { Pool } = require('pg');

const ENV = process.env, PROD = ENV.NODE_ENV === 'production';
/* tiny .env loader (no dependency): real environment variables win over the file */
for (const f of [path.join(__dirname, '..', '.env'), path.join(__dirname, '.env')]) {
  try { for (const l of fs.readFileSync(f, 'utf8').split(/\r?\n/)) { const m = l.match(/^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$/); if (m && ENV[m[1]] === undefined) ENV[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2'); } } catch (e) { /* no file: fine */ }
}
const ADMIN_EMAIL = (ENV.ADMIN_EMAIL || '').trim().toLowerCase();   /* never hard-coded: set ADMIN_EMAIL in the environment */
if (PROD && !ADMIN_EMAIL) throw new Error('ADMIN_EMAIL is required in production');
const SECRET = ENV.OTP_SECRET || (PROD ? '' : 'dev-only-secret');
if (!SECRET) throw new Error('OTP_SECRET is required in production');
const ROOT = path.join(__dirname, '..');
const WHATSAPP = (ENV.WHATSAPP_NUMBER || '919306539506').replace(/\D/g, '');   /* digits only, with country code */
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const hmac = s => crypto.createHmac('sha256', SECRET).update(s).digest('hex');
const eq = (a, b) => typeof a === 'string' && typeof b === 'string' && a.length === b.length && crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));
const SID = PROD ? '__Host-sid' : 'sid', csrfFor = t => hmac('csrf:' + t), emailH = e => hmac('email:' + e);

/* ---------- validation ---------- */
const LAYOUTS = ['list', 'skills', 'projects', 'experience', 'education', 'contact'];
const bad = m => Object.assign(new Error(m), { status: 400 });
const str = (v, max, name, req = false) => {
  if (v === undefined || v === null) v = '';
  if (typeof v !== 'string') throw bad(name + ' must be text');
  v = v.trim(); if (v.length > max) throw bad(name + ' is too long');
  if (req && !v) throw bad(name + ' is required'); return v;
};
const url = (v, name) => { v = str(v, 500, name); if (v && !/^(https?:\/\/[^\s]+|mailto:[^\s@]+@[^\s@]+)$/i.test(v)) throw bad(name + ' must be an http(s) or mailto link'); return v; };
const color = v => { v = str(v, 7, 'color'); if (!/^#[0-9a-fA-F]{6}$/.test(v)) throw bad('color must look like #00e5ff'); return v; };
const icon = v => { v = str(v, 20, 'icon'); if (!/^[a-z]{2,20}$/.test(v)) throw bad('icon is invalid'); return v; };
const slugify = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
const sectionIn = (b, partial) => {
  const o = {}, has = k => !partial || b[k] !== undefined;
  if (has('title')) o.title = str(b.title, 60, 'title', true);
  if (has('street')) o.street = str(b.street, 40, 'street name', true);
  if (has('color')) o.color = color(b.color || '#00e5ff');
  if (has('icon')) o.icon = icon(b.icon || 'folder');
  if (has('layout')) { if (!LAYOUTS.includes(b.layout || 'list')) throw bad('layout is invalid'); o.layout = b.layout || 'list'; }
  if (b.published !== undefined) o.published = !!b.published;
  return o;
};
const itemIn = (b, partial) => {
  const o = {}, has = k => !partial || b[k] !== undefined;
  if (has('title')) o.title = str(b.title, 120, 'title', true);
  if (has('body')) o.body = str(b.body, 2000, 'text');
  if (has('details')) o.details = str(b.details, 4000, 'details');
  if (has('icon')) o.icon = icon(b.icon || 'folder');
  if (has('url')) o.url = url(b.url, 'link');
  if (has('live_url')) o.live_url = url(b.live_url, 'live link');
  if (has('repo_url')) o.repo_url = url(b.repo_url, 'GitHub link');
  if (has('doc_url')) o.doc_url = url(b.doc_url, 'document link');
  if (b.published !== undefined) o.published = !!b.published;
  return o;
};
const settingsIn = b => {
  const h = b.hero || {}, s = b.site || {}, soc = b.socials;
  if (!Array.isArray(soc) || soc.length > 12) throw bad('socials must be a list of up to 12');
  const ph = Array.isArray(h.phrases) ? h.phrases.map(p => str(p, 60, 'phrase')).filter(Boolean).slice(0, 8) : [];
  if (!ph.length) throw bad('add at least one hero phrase');
  return {
    site: { title: str(s.title, 100, 'site title', true), description: str(s.description, 300, 'site description') },
    hero: { tag: str(h.tag, 40, 'hero tag'), name: str(h.name, 60, 'name', true), phrases: ph, lead: str(h.lead, 400, 'hero text'), cta: str(h.cta, 60, 'button label') },
    socials: soc.map(x => ({ label: str(x.label, 30, 'social label', true), icon: icon(x.icon || 'folder'), url: url(x.url, 'social link') })),
  };
};

/* element ids already used by the page: a section slug must never reuse one */
const RESERVED = new Set(['home', 'top', 'main', 'secs', 'dots', 'toast', 'tour', 'drive', 'panel', 'fast', 'choose', 'dash', 'wheel', 'modal', 'drawer', 'ans', 'prog', 'glow', 'cv', 'mm', 'dg', 'pt', 'ty', 'soc', 'exp', 'sq', 'sForm', 'connect', 'chat', 'admin', 'assets', 'api', 'sitemap', 'robots', 'favicon', 'original']);
try { for (const m of fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8').matchAll(/\sid="([A-Za-z][\w-]*)"/g)) RESERVED.add(m[1].toLowerCase()); } catch (e) { /* fixed list above still applies */ }

/* ---------- app factory ---------- */
function createApp({ pool, mail, llm = rag.makeLlm() }) {
  const app = express(), q = (t, p) => pool.query(t, p);
  app.disable('x-powered-by'); app.set('trust proxy', 1);
  app.use(compression());
  app.use(express.json({ limit: '20kb' })); app.use(cookieParser());
  app.use((req, res, next) => {
    res.set({ 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin', 'X-Frame-Options': 'DENY', 'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()', 'Cross-Origin-Opener-Policy': 'same-origin', 'Cross-Origin-Resource-Policy': 'same-origin', ...(PROD ? { 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains' } : {}),
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' blob: data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" });
    next();
  });
  const wrap = f => (req, res, next) => Promise.resolve(f(req, res, next)).catch(next);
  const audit = (action, detail = '') => q('insert into audit_events(action,detail) values($1,$2)', [action, String(detail).slice(0, 200)]);

  const hits = new Map();
  const limit = (name, max, ms, keyFn = r => r.ip) => (req, res, next) => {
    const k = name + ':' + keyFn(req), now = Date.now(), e = (hits.get(k) || []).filter(t => now - t < ms);
    if (e.length >= max) return res.status(429).json({ error: 'Too many requests. Try again later.' });
    e.push(now); hits.set(k, e); next();
  };

  app.get('/api/health', wrap(async (req, res) => { await q('select 1'); res.json({ ok: true }); }));

  /* ----- public content (published only) ----- */
  app.get('/api/public/content', wrap(async (req, res) => {
    const st = await q('select key,value from settings'), settings = Object.fromEntries(st.rows.map(r => [r.key, r.value]));
    const secs = await q('select id,slug,title,street,color,icon,layout from sections where published order by position,id');
    const its = await q('select i.section_id,i.title,i.body,i.details,i.icon,i.url,i.live_url,i.repo_url,i.doc_url from items i join sections s on s.id=i.section_id where i.published and s.published order by i.position,i.id');
    const sections = secs.rows.map(({ id, ...s }) => ({ ...s, items: its.rows.filter(i => i.section_id === id).map(({ section_id, ...i }) => i) }));
    res.set('Cache-Control', 'public, max-age=30, stale-while-revalidate=300').json({ settings, sections });
  }));

  /* ----- admin auth: hashed e-mail, hashed OTP, hashed session token, one session at a time ----- */
  const mask = e => e ? e.replace(/^(.).*@(.).*(\.[^.]+)$/, '$1***@$2***$3') : '(not set)';
  const OTP_COOLDOWN = 30e3;   /* resend allowed after 30 seconds */
  const noStore = (req, res, next) => { res.set('Cache-Control', 'no-store'); next(); };
  app.use('/api/admin', noStore);
  app.post('/api/admin/auth/request-otp', limit('otp-ip', 20, 3600e3), limit('otp-all', 20, 3600e3, () => 'all'), wrap(async (req, res) => {
    /* the owner never types an address: the code always goes to ADMIN_EMAIL from the environment */
    const generic = { ok: true, message: 'A code has been sent.', resendAfter: OTP_COOLDOWN / 1000 };
    if (!ADMIN_EMAIL) {   /* the browser always gets the same answer; the reason is only written to YOUR terminal */
      console.warn(PROD ? '[auth] login code request rejected' : '[auth hint] No code sent: ADMIN_EMAIL is not set. Put ADMIN_EMAIL=you@example.com in .env (project root) and restart.');
      return res.json(generic);
    }
    const eh = emailH(ADMIN_EMAIL), last = await q('select created_at from otp_challenges where email_h=$1 order by id desc limit 1', [eh]);
    if (last.rows[0] && Date.now() - last.rows[0].created_at < OTP_COOLDOWN) { if (!PROD) console.warn('[auth hint] No new code sent: a code was already sent less than 30 s ago. Use that one or wait a moment.'); return res.json(generic); }
    const code = String(crypto.randomInt(0, 1e6)).padStart(6, '0');
    await q("delete from otp_challenges where expires_at < now() - interval '1 day'");
    await q("insert into otp_challenges(email_h,code_hash,expires_at) values($1,$2,now()+interval '10 minutes')", [eh, hmac('otp:' + eh + ':' + code)]);
    try { await mail.sendOtp(ADMIN_EMAIL, code); if (ENV.BREVO_API_KEY) console.log(`[auth] login code emailed via Brevo to ${mask(ADMIN_EMAIL)} (it is NOT printed here when Brevo is configured)`); } catch (e) { console.error('OTP email failed:', e.message, ENV.BREVO_API_KEY ? '- check BREVO_API_KEY and that BREVO_SENDER_EMAIL is a verified sender in Brevo' : ''); }
    res.json(generic);
  }));
  app.post('/api/admin/auth/verify-otp', limit('verify-ip', 20, 3600e3), wrap(async (req, res) => {
    const code = str(req.body.code, 6, 'code'), fail = () => res.status(401).json({ error: 'Invalid or expired code.' });
    if (!ADMIN_EMAIL || !/^\d{6}$/.test(code)) return fail();
    const eh = emailH(ADMIN_EMAIL), r = await q('select * from otp_challenges where email_h=$1 and consumed_at is null and expires_at>now() order by id desc limit 1', [eh]), c = r.rows[0];
    if (!c || c.attempts >= 5) return fail();
    await q('update otp_challenges set attempts=attempts+1 where id=$1', [c.id]);
    if (!eq(c.code_hash, hmac('otp:' + eh + ':' + code))) return fail();
    await q('update otp_challenges set consumed_at=now() where id=$1', [c.id]);
    await q('update admin_sessions set revoked=true where not revoked');                       /* every login starts a brand-new session */
    const token = crypto.randomBytes(32).toString('hex');
    await q("insert into admin_sessions(token_hash,csrf,expires_at) values($1,'',now()+interval '2 hours')", [sha(token)]);
    res.cookie(SID, token, { httpOnly: true, sameSite: 'strict', secure: PROD, path: '/' });   /* session cookie: gone when the browser closes */
    await audit('login'); res.json({ ok: true, csrf: csrfFor(token) });
  }));

  const auth = wrap(async (req, res, next) => {
    res.set('Cache-Control', 'no-store');
    const t = req.cookies[SID]; if (!t || typeof t !== 'string') return res.status(401).json({ error: 'Not signed in' });
    const r = await q("select * from admin_sessions where token_hash=$1 and not revoked and expires_at>now() and last_seen>now()-interval '20 minutes'", [sha(t)]), s = r.rows[0];
    if (!s) return res.status(401).json({ error: 'Not signed in' });
    if (!['GET', 'HEAD'].includes(req.method)) {
      const o = req.get('origin'); if (o && new URL(o).host !== req.get('host')) return res.status(403).json({ error: 'Bad origin' });
      const h = req.get('x-csrf-token') || ''; if (!h || !eq(h, csrfFor(t))) return res.status(403).json({ error: 'Missing or invalid CSRF token' });
    }
    await q('update admin_sessions set last_seen=now() where token_hash=$1', [s.token_hash]);
    req.session = s; req.sid = t; next();
  });
  app.get('/api/admin/auth/me', auth, (req, res) => res.json({ ok: true, csrf: csrfFor(req.sid) }));
  app.post('/api/admin/auth/logout', auth, wrap(async (req, res) => {
    await q('update admin_sessions set revoked=true where not revoked');                       /* revoke every session, not just this one */
    res.clearCookie(SID, { path: '/', httpOnly: true, sameSite: 'strict', secure: PROD });
    if (PROD) res.set('Clear-Site-Data', '"cache", "storage"');
    await audit('logout'); res.json({ ok: true });
  }));

  /* ----- public AI search / assistant (profile-only RAG) ----- */
  const contactLine = async () => { const r = await q("select value from settings where key='socials'"); const s = (r.rows[0] && r.rows[0].value) || []; const m = s.find(x => /^mailto:/i.test(x.url)); return m ? m.url.replace(/^mailto:/i, '') : ''; };
  app.post('/api/assistant/query', limit('ai-ip', 12, 600e3), limit('ai-all', 1500, 86400e3, () => 'all'), wrap(async (req, res) => {
    if (typeof req.body.q !== 'string') throw bad('question must be text');
    res.set('Cache-Control', 'no-store').json(await rag.ask({ pool, llm, q: req.body.q, contact: await contactLine(), daily: Number(ENV.LLM_DAILY_LIMIT) || 300 }));
  }));
  app.get('/api/search', limit('search-ip', 60, 60e3), wrap(async (req, res) => {
    const text = typeof req.query.q === 'string' ? req.query.q.slice(0, 200) : '';
    const rows = await rag.retrieve(pool, text, 8);
    res.set('Cache-Control', 'no-store').json({ results: rows.map(r => ({ title: r.title, section: r.section_slug, snippet: rag.snippet(r.content.replace(/^[^:]*:\s*/, ''), 160), url: r.url })) });
  }));

  /* ----- contact form + private visitor chat ----- */
  const SITE = req => (ENV.SITE_URL || (req.protocol + '://' + req.get('host'))).replace(/\/+$/, '');
  const missing = () => Object.assign(new Error('Not found'), { status: 404 });
  const EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;
  const clean1 = t => String(t).replace(/[\r\n]+/g, ' ');
  app.post('/api/contact', limit('contact-ip', 5, 3600e3), limit('contact-all', 100, 86400e3, () => 'all'), wrap(async (req, res) => {
    if (req.body.website) return res.status(201).json({ ok: true });   /* hidden trap field: only bots fill it, they get a fake success */
    const name = str(req.body.name, 80, 'name', true), email = str(req.body.email, 200, 'email', true).toLowerCase(), message = str(req.body.message, 3000, 'message', true);
    if (!EMAIL_RE.test(email)) throw bad('enter a valid email address');
    const r = await q('insert into contact_messages(name,email,message) values($1,$2,$3) returning id', [name, email, message]);
    if (ADMIN_EMAIL) { try { await mail.sendContact(ADMIN_EMAIL, { name: clean1(name), email, message }); } catch (e) { console.error('contact email failed:', e.message); } }
    await audit('contact.new', 'message #' + r.rows[0].id); res.status(201).json({ ok: true });
  }));

  const chatOf = async token => {
    if (typeof token !== 'string' || !/^[A-Za-z0-9_-]{20,64}$/.test(token)) throw missing();
    const r = await q('select c.*, m.name, m.email from chats c join contact_messages m on m.id=c.message_id where c.token_hash=$1', [sha(token)]);
    if (!r.rows[0]) throw missing(); return r.rows[0];
  };
  const postsOf = async (chatId, after) => (await q('select id,sender,body,created_at from chat_posts where chat_id=$1 and id>$2 order by id limit 200', [chatId, after])).rows;
  const afterOf = req => Math.max(0, parseInt(req.query.after, 10) || 0);
  const byToken = r => String(r.params.token).slice(0, 16);
  app.get('/api/chat/:token', limit('chat-get', 300, 60e3, byToken), wrap(async (req, res) => {
    const c = await chatOf(req.params.token);
    res.set('Cache-Control', 'no-store').json({ name: c.name, status: c.status, posts: await postsOf(c.id, afterOf(req)) });
  }));
  app.post('/api/chat/:token/post', limit('chat-post', 20, 60e3, byToken), wrap(async (req, res) => {
    const c = await chatOf(req.params.token);
    if (c.status !== 'open') return res.status(409).json({ error: 'This chat has been closed.' });
    const body = str(req.body.body, 1000, 'message', true);
    if ((await q('select count(*)::int n from chat_posts where chat_id=$1', [c.id])).rows[0].n >= 1000) return res.status(429).json({ error: 'This chat is full.' });
    const r = await q("insert into chat_posts(chat_id,sender,body) values($1,'visitor',$2) returning id,sender,body,created_at", [c.id, body]);
    if (ADMIN_EMAIL && (!c.notified_at || Date.now() - c.notified_at > 10 * 60e3)) {   /* at most one "new chat message" e-mail per chat every 10 minutes */
      await q('update chats set notified_at=now() where id=$1', [c.id]);
      try { await mail.sendChatNotice(ADMIN_EMAIL, { name: clean1(c.name), body }); } catch (e) { console.error('chat notice failed:', e.message); }
    }
    res.status(201).json(r.rows[0]);
  }));

  /* admin side of the inbox: mounted before the content router so chat traffic never triggers a search re-index */
  const MS = express.Router(), CH = express.Router();
  app.use('/api/admin/messages', auth, MS); app.use('/api/admin/chats', auth, CH);
  const rid = req => { const n = Number(req.params.id); if (!Number.isInteger(n) || n < 1) throw bad('bad id'); return n; };
  MS.get('/', wrap(async (req, res) => {
    const r = await q(`select m.id,m.name,m.email,m.message,m.is_read,m.created_at,c.id chat_id,c.status chat_status,c.invited_at,
      (select count(*)::int from chat_posts p where p.chat_id=c.id and p.sender='visitor' and p.id>c.admin_seen) unread
      from contact_messages m left join chats c on c.message_id=m.id order by m.id desc limit 300`);
    res.json(r.rows);
  }));
  MS.post('/:id/read', wrap(async (req, res) => { await q('update contact_messages set is_read=true where id=$1', [rid(req)]); res.json({ ok: true }); }));
  MS.post('/:id/invite', wrap(async (req, res) => {
    const m = (await q('select * from contact_messages where id=$1', [rid(req)])).rows[0]; if (!m) throw missing();
    const token = crypto.randomBytes(24).toString('base64url'), link = SITE(req) + '/chat/' + token;
    try { await mail.sendChatInvite(m.email, { name: clean1(m.name), link }); } catch (e) { console.error('chat invite email failed:', e.message); return res.status(502).json({ error: 'The invite email could not be sent. Check the Brevo settings.' }); }
    const up = await q("update chats set token_hash=$1,status='open',closed_at=null,invited_at=now() where message_id=$2 returning id", [sha(token), m.id]);
    const id = up.rows[0] ? up.rows[0].id : (await q('insert into chats(message_id,token_hash) values($1,$2) returning id', [m.id, sha(token)])).rows[0].id;
    await q('update contact_messages set is_read=true where id=$1', [m.id]);
    await audit('chat.invite', 'message #' + m.id); res.json({ ok: true, chat_id: id });
  }));
  MS.delete('/:id', wrap(async (req, res) => { const r = await q('delete from contact_messages where id=$1 returning id', [rid(req)]); if (!r.rowCount) throw missing(); await audit('contact.delete', 'message #' + r.rows[0].id); res.json({ ok: true }); }));
  const adminChat = async req => { const c = (await q('select c.*, m.name, m.email from chats c join contact_messages m on m.id=c.message_id where c.id=$1', [rid(req)])).rows[0]; if (!c) throw missing(); return c; };
  CH.get('/:id', wrap(async (req, res) => {
    const c = await adminChat(req), posts = await postsOf(c.id, afterOf(req));
    const top = (await q('select coalesce(max(id),0)::int m from chat_posts where chat_id=$1', [c.id])).rows[0].m;
    await q('update chats set admin_seen=$1 where id=$2', [top, c.id]);
    res.json({ id: c.id, name: c.name, email: c.email, status: c.status, posts });
  }));
  CH.post('/:id/post', wrap(async (req, res) => {
    const c = await adminChat(req); if (c.status !== 'open') return res.status(409).json({ error: 'This chat is closed.' });
    const body = str(req.body.body, 1000, 'message', true);
    res.status(201).json((await q("insert into chat_posts(chat_id,sender,body) values($1,'admin',$2) returning id,sender,body,created_at", [c.id, body])).rows[0]);
  }));
  CH.post('/:id/close', wrap(async (req, res) => {
    const c = await adminChat(req); await q("update chats set status='closed',closed_at=now() where id=$1", [c.id]);
    await audit('chat.close', 'chat #' + c.id); res.json({ ok: true });
  }));

  /* ----- admin content ----- */
  const A = express.Router(); A.use(auth); app.use('/api/admin', A);
  let rt; const scheduleReindex = () => { clearTimeout(rt); rt = setTimeout(() => rag.reindex(pool).catch(e => console.error('reindex failed:', e.message)), 1500); if (rt.unref) rt.unref(); };
  A.use((req, res, next) => { if (!['GET', 'HEAD'].includes(req.method)) res.on('finish', () => { if (res.statusCode < 300) scheduleReindex(); }); next(); });
  A.post('/rag/reindex', wrap(async (req, res) => { const n = await rag.reindex(pool); await audit('rag-reindex', n + ' chunks'); res.json({ ok: true, chunks: n }); }));
  A.get('/rag/status', wrap(async (req, res) => { const c = await q('select count(*)::int n from rag_chunks'), u = await q('select calls from rag_usage where day=current_date'); res.json({ chunks: c.rows[0].n, llmConfigured: !!llm, callsToday: u.rows[0] ? u.rows[0].calls : 0 }); }));
  const id = req => { const n = Number(req.params.id); if (!Number.isInteger(n) || n < 1) throw bad('bad id'); return n; };
  const setSql = (o, start = 1) => { const k = Object.keys(o); return { sql: k.map((c, i) => `${c}=$${i + start}`).join(','), vals: k.map(c => o[c]) }; };
  const notFound = () => Object.assign(new Error('Not found'), { status: 404 });

  A.get('/settings', wrap(async (req, res) => { const r = await q('select key,value from settings'); res.json(Object.fromEntries(r.rows.map(x => [x.key, x.value]))); }));
  A.put('/settings', wrap(async (req, res) => {
    const s = settingsIn(req.body);
    for (const k of Object.keys(s)) await q('insert into settings(key,value) values($1,$2) on conflict(key) do update set value=$2', [k, JSON.stringify(s[k])]);
    await audit('settings.update'); res.json(s);
  }));
  A.get('/sections', wrap(async (req, res) => {
    const s = await q('select * from sections order by position,id'), i = await q('select * from items order by position,id');
    res.json(s.rows.map(x => ({ ...x, items: i.rows.filter(y => y.section_id === x.id) })));
  }));
  A.post('/sections', wrap(async (req, res) => {
    const o = sectionIn(req.body); let slug = slugify(str(req.body.slug || o.title, 60, 'slug')) || 'section';
    if (RESERVED.has(slug)) slug = 's-' + slug;
    const exists = await q('select 1 from sections where slug=$1', [slug]); if (exists.rowCount) slug += '-' + crypto.randomInt(100, 999);
    const pos = (await q('select coalesce(max(position),0)+1 p from sections')).rows[0].p;
    const r = await q('insert into sections(slug,title,street,color,icon,layout,position,published) values($1,$2,$3,$4,$5,$6,$7,$8) returning *',
      [slug, o.title, o.street, o.color, o.icon, o.layout, pos, o.published !== false]);
    await audit('section.create', slug); res.status(201).json({ ...r.rows[0], items: [] });
  }));
  A.patch('/sections/:id', wrap(async (req, res) => {
    const o = sectionIn(req.body, true), n = Object.keys(o).length; if (!n) throw bad('nothing to update');
    const { sql, vals } = setSql(o), r = await q(`update sections set ${sql},updated_at=now() where id=$${n + 1} returning *`, [...vals, id(req)]);
    if (!r.rowCount) throw notFound(); await audit('section.update', r.rows[0].slug); res.json(r.rows[0]);
  }));
  A.delete('/sections/:id', wrap(async (req, res) => {
    const r = await q('delete from sections where id=$1 returning slug', [id(req)]); if (!r.rowCount) throw notFound();
    await audit('section.delete', r.rows[0].slug); res.json({ ok: true });
  }));
  const reorder = (table, scope) => wrap(async (req, res) => {
    const ids = req.body.ids; if (!Array.isArray(ids) || !ids.every(Number.isInteger) || ids.length > 500) throw bad('ids must be a list of numbers');
    const sc = scope ? Number(req.body.section_id) : null;
    for (let p = 0; p < ids.length; p++) await q(`update ${table} set position=$1 where id=$2${scope ? ' and section_id=$3' : ''}`, scope ? [p + 1, ids[p], sc] : [p + 1, ids[p]]);
    await audit(table + '.reorder'); res.json({ ok: true });
  });
  A.post('/sections/reorder', reorder('sections', false));
  A.post('/items/reorder', reorder('items', true));
  A.post('/items', wrap(async (req, res) => {
    const o = itemIn(req.body), sid = Number(req.body.section_id);
    if (!(await q('select 1 from sections where id=$1', [sid])).rowCount) throw bad('section not found');
    const pos = (await q('select coalesce(max(position),0)+1 p from items where section_id=$1', [sid])).rows[0].p;
    const r = await q('insert into items(section_id,title,body,details,icon,url,live_url,repo_url,doc_url,position,published) values($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) returning *',
      [sid, o.title, o.body, o.details, o.icon, o.url, o.live_url || '', o.repo_url || '', o.doc_url || '', pos, o.published !== false]);
    await audit('item.create', o.title); res.status(201).json(r.rows[0]);
  }));
  A.patch('/items/:id', wrap(async (req, res) => {
    const o = itemIn(req.body, true); if (req.body.section_id !== undefined) {
      const sid = Number(req.body.section_id); if (!(await q('select 1 from sections where id=$1', [sid])).rowCount) throw bad('section not found'); o.section_id = sid; }
    const n = Object.keys(o).length; if (!n) throw bad('nothing to update');
    const { sql, vals } = setSql(o), r = await q(`update items set ${sql},updated_at=now() where id=$${n + 1} returning *`, [...vals, id(req)]);
    if (!r.rowCount) throw notFound(); await audit('item.update', r.rows[0].title); res.json(r.rows[0]);
  }));
  A.delete('/items/:id', wrap(async (req, res) => {
    const r = await q('delete from items where id=$1 returning title', [id(req)]); if (!r.rowCount) throw notFound();
    await audit('item.delete', r.rows[0].title); res.json({ ok: true });
  }));
  A.get('/audit-log', wrap(async (req, res) => res.json((await q('select id,action,detail,created_at from audit_events order by id desc limit 100')).rows)));

  /* ----- static site + one page per section ----- */
  app.use('/api', (req, res) => res.status(404).json({ error: 'Not found' }));
  app.use('/admin', express.static(path.join(ROOT, 'admin')));
  app.get('/favicon.ico', (req, res) => res.set('Cache-Control', 'public, max-age=86400').sendFile(path.join(ROOT, 'assets', 'icons', 'android-chrome-192x192.png')));
  app.use('/assets', express.static(path.join(ROOT, 'assets'), { maxAge: '30d', immutable: true }));
  const attr = t => String(t).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  const indexSrc = () => fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  /* the same index.html shell serves every page: the server only tells it which page to show and fixes the title / description / canonical link for search engines */
  const sendPage = (req, res, { page = '', title, desc, urlPath = '/' }) => {
    let h = indexSrc(); const extra = page === 'connect' ? `;window.__WA__=${JSON.stringify(WHATSAPP)}` : '';
    if (title) h = h.replace(/<title>[^<]*<\/title>/, () => '<title>' + attr(title) + '</title>');
    if (desc) h = h.replace(/(<meta name="description" content=")[^"]*(">)/, (m, a, b) => a + attr(desc) + b);
    h = h.replace('<meta charset="utf-8">', () => `<meta charset="utf-8">\n<script>window.__PAGE__=${JSON.stringify(page).replace(/</g, '\\u003c')}${extra}</script>\n<link rel="canonical" href="${attr(SITE(req) + urlPath)}">`);
    res.set('Cache-Control', 'no-cache').type('html').send(h);
  };
  const siteName = async () => { const r = await q("select value from settings where key='site'"); return (r.rows[0] && r.rows[0].value && r.rows[0].value.title) || 'Ravi Dhiman'; };
  app.get('/', (req, res) => sendPage(req, res, {}));
  app.get('/connect', wrap(async (req, res) => { const n = await siteName(); sendPage(req, res, { page: 'connect', title: 'Connect — ' + n, desc: 'Send a message or reach out on WhatsApp.', urlPath: '/connect' }); }));
  app.get('/chat/:token', (req, res) => res.set({ 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' }).sendFile(path.join(ROOT, 'chat', 'index.html')));
  app.get('/robots.txt', (req, res) => res.type('text/plain').send(`User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\nDisallow: /chat/\n\nSitemap: ${SITE(req)}/sitemap.xml\n`));
  app.get('/sitemap.xml', wrap(async (req, res) => {
    const base = SITE(req), secs = await q('select s.slug, greatest(s.updated_at, coalesce(max(i.updated_at), s.updated_at)) m from sections s left join items i on i.section_id=s.id where s.published group by s.id order by s.position,s.id');
    const day = d => new Date(d).toISOString().slice(0, 10), top = secs.rows.reduce((a, r) => (r.m > a ? r.m : a), new Date(0));
    const url = (p, d, pr) => `  <url><loc>${attr(base + p)}</loc>${d ? `<lastmod>${day(d)}</lastmod>` : ''}<priority>${pr}</priority></url>`;
    res.type('application/xml').send(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${[url('/', top.getTime() ? top : null, '1.0'), ...secs.rows.map(r => url('/' + r.slug, r.m, '0.8')), url('/connect', null, '0.6')].join('\n')}\n</urlset>\n`);
  }));
  app.get('/:slug', wrap(async (req, res, next) => {
    const r = await q('select slug,title from sections where published and slug=$1', [req.params.slug]); if (!r.rows[0]) return next();
    const n = await siteName(); sendPage(req, res, { page: r.rows[0].slug, title: r.rows[0].title + ' — ' + n, desc: `${r.rows[0].title} — ${n}. Explore the portfolio or take the wheel in Drive Mode.`, urlPath: '/' + r.rows[0].slug });
  }));
  app.use((req, res, next) => { if (req.method !== 'GET' && req.method !== 'HEAD') return next(); res.status(404).type('html').send('<!DOCTYPE html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found</title><link rel="icon" href="/assets/icons/android-chrome-192x192.png"><body style="margin:0;min-height:100vh;display:grid;place-items:center;background:#05060f;color:#e8ecff;font:16px system-ui,sans-serif;text-align:center"><div><h1 style="margin:0 0 8px">Page not found</h1><a href="/" style="color:#00e5ff">Back to the portfolio</a></div>'); });
  app.use((err, req, res, next) => {
    if (err.type === 'entity.parse.failed') return res.status(400).json({ error: 'Invalid JSON' });
    if (err.status && err.status < 500) return res.status(err.status).json({ error: err.message });
    console.error(err.message); res.status(500).json({ error: 'Something went wrong' });
  });
  return app;
}

/* ---------- migrations, seed, mail ---------- */
async function migrate(pool) {
  await pool.query('create table if not exists schema_migrations(name text primary key)');
  for (const f of fs.readdirSync(path.join(__dirname, 'migrations')).sort()) {
    if ((await pool.query('select 1 from schema_migrations where name=$1', [f])).rowCount) continue;
    await pool.query(fs.readFileSync(path.join(__dirname, 'migrations', f), 'utf8'));
    await pool.query('insert into schema_migrations(name) values($1)', [f]);
  }
}
async function seed(pool) {
  if ((await pool.query('select 1 from sections limit 1')).rowCount || (await pool.query('select 1 from settings limit 1')).rowCount) return false;
  const d = JSON.parse(fs.readFileSync(path.join(__dirname, 'seed.json'), 'utf8'));
  for (const [k, v] of Object.entries(d.settings)) await pool.query('insert into settings(key,value) values($1,$2)', [k, JSON.stringify(v)]);
  let p = 0;
  for (const s of d.sections) {
    const r = await pool.query('insert into sections(slug,title,street,color,icon,layout,position) values($1,$2,$3,$4,$5,$6,$7) returning id', [s.slug, s.title, s.street, s.color, s.icon, s.layout, ++p]);
    let n = 0; for (const [t, b, i, u, dt] of s.items) await pool.query('insert into items(section_id,title,body,icon,url,details,position) values($1,$2,$3,$4,$5,$6,$7)', [r.rows[0].id, t, b, i, u, dt, ++n]);
  }
  return true;
}
function makeMailer() {
  const key = ENV.BREVO_API_KEY, api = ENV.BREVO_API_URL || 'https://api.brevo.com/v3/smtp/email';
  const send = async ({ to, subject, text, replyTo, senderName = 'Portfolio', dev }) => {
    if (!key) { if (PROD) throw new Error('BREVO_API_KEY is not configured'); console.log(dev || `[dev only] email to ${to}: ${subject}\n${text}`); return; }
    const r = await fetch(api, { method: 'POST', headers: { 'api-key': key, 'content-type': 'application/json' }, body: JSON.stringify({
      sender: { email: ENV.BREVO_SENDER_EMAIL, name: senderName }, to: [{ email: to }], ...(replyTo ? { replyTo } : {}), subject, textContent: text }) });
    if (!r.ok) throw new Error('Brevo responded ' + r.status);
  };
  return {
    sendOtp: (to, code) => send({ to, senderName: 'Portfolio Admin', subject: 'Your admin login code', dev: `[dev only] admin login code: ${code}`,
      text: `Your login code is ${code}. It expires in 10 minutes. If you did not request it, ignore this email.` }),
    sendContact: (to, m) => send({ to, senderName: 'Portfolio Contact', replyTo: { email: m.email, name: m.name }, subject: `New message from ${m.name}`,
      text: `You received a new message through your portfolio contact form.\n\nName: ${m.name}\nEmail: ${m.email}\n\nMessage:\n${m.message}\n\nOpen the admin page (Messages) to read it and send a chat invite. You can also reply to this email directly.` }),
    sendChatInvite: (to, { name, link }) => send({ to, senderName: 'Ravi Dhiman', subject: 'Chat with Ravi Dhiman',
      text: `Hi ${name},\n\nThanks for reaching out. Ravi has opened a private chat with you. Use this link to join:\n\n${link}\n\nThis link is only for you, so please do not share it.\n\nRavi Dhiman` }),
    sendChatNotice: (to, { name, body }) => send({ to, senderName: 'Portfolio Chat', subject: `New chat message from ${name}`,
      text: `${name} wrote in your chat:\n\n${body}\n\nOpen the admin page (Messages) to reply. You get at most one of these emails every 10 minutes per chat.` }),
  };
}
module.exports = { createApp, migrate, seed, makeMailer, rag };

if (require.main === module) {
  const pool = new Pool({ connectionString: ENV.DATABASE_URL });
  migrate(pool).then(() => seed(pool)).then(() => rag.reindex(pool)).then(() => {
    const port = Number(ENV.PORT) || 3000;
    createApp({ pool, mail: makeMailer() }).listen(port, () => {
      const m = ADMIN_EMAIL ? ADMIN_EMAIL.replace(/^(.).*@(.).*(\.[^.]+)$/, '$1***@$2***$3') : 'NOT SET - admin login disabled';
      console.log('Portfolio server on :' + port);
      console.log(`  admin e-mail : ${m}\n  login codes  : ${ENV.BREVO_API_KEY ? 'emailed via Brevo' : (PROD ? 'Brevo NOT configured (login will fail)' : 'printed in this terminal (dev mode)')}\n  AI assistant : ${ENV.LLM_BASE_URL && ENV.LLM_API_KEY && ENV.LLM_MODEL ? 'model configured' : 'search-only (no LLM_ settings)'}`);
    });
  }).catch(e => { console.error('Startup failed:', e.message); process.exit(1); });
}
