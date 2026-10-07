'use strict';
const express = require('express'), cookieParser = require('cookie-parser'), crypto = require('crypto');
const fs = require('fs'), path = require('path'), { Pool } = require('pg');

const ENV = process.env, PROD = ENV.NODE_ENV === 'production';
const ADMIN_EMAIL = (ENV.ADMIN_EMAIL || 'ravidhiman8673@gmail.com').toLowerCase();
const SECRET = ENV.OTP_SECRET || (PROD ? '' : 'dev-only-secret');
if (!SECRET) throw new Error('OTP_SECRET is required in production');
const ROOT = path.join(__dirname, '..');
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const hmac = s => crypto.createHmac('sha256', SECRET).update(s).digest('hex');
const eq = (a, b) => a.length === b.length && crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));

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
const RESERVED = new Set(['home', 'top', 'main', 'secs', 'dots', 'toast', 'tour', 'drive', 'panel', 'fast', 'choose', 'dash', 'wheel', 'modal', 'drawer', 'ans', 'prog', 'glow', 'cv', 'mm', 'dg', 'pt', 'ty', 'soc', 'exp', 'sq', 'sForm']);
try { for (const m of fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8').matchAll(/\sid="([A-Za-z][\w-]*)"/g)) RESERVED.add(m[1].toLowerCase()); } catch (e) { /* fixed list above still applies */ }

/* ---------- app factory ---------- */
function createApp({ pool, mail }) {
  const app = express(), q = (t, p) => pool.query(t, p);
  app.disable('x-powered-by'); app.set('trust proxy', 1);
  app.use(express.json({ limit: '100kb' })); app.use(cookieParser());
  app.use((req, res, next) => {
    res.set({ 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin', 'X-Frame-Options': 'DENY',
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" });
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
    const its = await q('select i.section_id,i.title,i.body,i.details,i.icon,i.url from items i join sections s on s.id=i.section_id where i.published and s.published order by i.position,i.id');
    const sections = secs.rows.map(s => ({ ...s, items: its.rows.filter(i => i.section_id === s.id).map(({ section_id, ...i }) => i) }));
    res.set('Cache-Control', 'public, max-age=30').json({ settings, sections });
  }));

  /* ----- admin auth ----- */
  app.post('/api/admin/auth/request-otp', limit('otp-ip', 10, 3600e3), wrap(async (req, res) => {
    const email = str(req.body.email, 200, 'email').toLowerCase(), generic = { ok: true, message: 'If this address is allowed, a code has been sent.' };
    if (email !== ADMIN_EMAIL) return res.json(generic);
    const last = await q('select created_at from otp_challenges where email=$1 order by id desc limit 1', [email]);
    if (last.rows[0] && Date.now() - last.rows[0].created_at < 60e3) return res.json(generic);
    const code = String(crypto.randomInt(0, 1e6)).padStart(6, '0');
    await q("insert into otp_challenges(email,code_hash,expires_at) values($1,$2,now()+interval '10 minutes')", [email, hmac(email + ':' + code)]);
    try { await mail.sendOtp(email, code); } catch (e) { console.error('OTP email failed:', e.message); }
    res.json(generic);
  }));
  app.post('/api/admin/auth/verify-otp', limit('verify-ip', 20, 3600e3), wrap(async (req, res) => {
    const email = str(req.body.email, 200, 'email').toLowerCase(), code = str(req.body.code, 6, 'code'), fail = () => res.status(401).json({ error: 'Invalid or expired code.' });
    if (email !== ADMIN_EMAIL || !/^\d{6}$/.test(code)) return fail();
    const r = await q('select * from otp_challenges where email=$1 and consumed_at is null and expires_at>now() order by id desc limit 1', [email]), c = r.rows[0];
    if (!c || c.attempts >= 5) return fail();
    await q('update otp_challenges set attempts=attempts+1 where id=$1', [c.id]);
    if (!eq(c.code_hash, hmac(email + ':' + code))) return fail();
    await q('update otp_challenges set consumed_at=now() where id=$1', [c.id]);
    const token = crypto.randomBytes(32).toString('hex'), csrf = crypto.randomBytes(24).toString('hex');
    await q("insert into admin_sessions(token_hash,csrf,expires_at) values($1,$2,now()+interval '8 hours')", [sha(token), csrf]);
    res.cookie('sid', token, { httpOnly: true, sameSite: 'strict', secure: PROD, maxAge: 8 * 3600e3, path: '/' });
    await audit('login'); res.json({ ok: true, csrf });
  }));

  const auth = wrap(async (req, res, next) => {
    const t = req.cookies.sid; if (!t) return res.status(401).json({ error: 'Not signed in' });
    const r = await q('select * from admin_sessions where token_hash=$1 and not revoked and expires_at>now()', [sha(t)]), s = r.rows[0];
    if (!s) return res.status(401).json({ error: 'Not signed in' });
    if (!['GET', 'HEAD'].includes(req.method)) {
      const o = req.get('origin'); if (o && new URL(o).host !== req.get('host')) return res.status(403).json({ error: 'Bad origin' });
      const h = req.get('x-csrf-token') || ''; if (!h || !eq(h, s.csrf)) return res.status(403).json({ error: 'Missing or invalid CSRF token' });
    }
    req.session = s; next();
  });
  app.get('/api/admin/auth/me', auth, (req, res) => res.json({ email: ADMIN_EMAIL, csrf: req.session.csrf }));
  app.post('/api/admin/auth/logout', auth, wrap(async (req, res) => {
    await q('update admin_sessions set revoked=true where token_hash=$1', [req.session.token_hash]);
    res.clearCookie('sid', { path: '/' }); await audit('logout'); res.json({ ok: true });
  }));

  /* ----- admin content ----- */
  const A = express.Router(); A.use(auth); app.use('/api/admin', A);
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
    const r = await q('insert into items(section_id,title,body,details,icon,url,position,published) values($1,$2,$3,$4,$5,$6,$7,$8) returning *',
      [sid, o.title, o.body, o.details, o.icon, o.url, pos, o.published !== false]);
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

  /* ----- static site ----- */
  app.use('/api', (req, res) => res.status(404).json({ error: 'Not found' }));
  app.use('/admin', express.static(path.join(ROOT, 'admin')));
  app.get('/', (req, res) => res.sendFile(path.join(ROOT, 'index.html')));
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
  return { async sendOtp(to, code) {
    if (!key) { if (PROD) throw new Error('BREVO_API_KEY is not configured'); console.log(`[dev only] admin login code: ${code}`); return; }
    const r = await fetch(api, { method: 'POST', headers: { 'api-key': key, 'content-type': 'application/json' }, body: JSON.stringify({
      sender: { email: ENV.BREVO_SENDER_EMAIL, name: 'Portfolio Admin' }, to: [{ email: to }], subject: 'Your admin login code',
      textContent: `Your login code is ${code}. It expires in 10 minutes. If you did not request it, ignore this email.` }) });
    if (!r.ok) throw new Error('Brevo responded ' + r.status);
  } };
}
module.exports = { createApp, migrate, seed, makeMailer };

if (require.main === module) {
  const pool = new Pool({ connectionString: ENV.DATABASE_URL });
  migrate(pool).then(() => seed(pool)).then(() => {
    const port = Number(ENV.PORT) || 3000;
    createApp({ pool, mail: makeMailer() }).listen(port, () => console.log('Portfolio server on :' + port));
  }).catch(e => { console.error('Startup failed:', e.message); process.exit(1); });
}
