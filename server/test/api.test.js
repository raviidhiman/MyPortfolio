process.env.ADMIN_EMAIL = 'owner@example.test'; process.env.OTP_SECRET = 'test-secret';
const { test, before, after } = require('node:test'); const assert = require('node:assert');
const { Pool } = require('pg'); const { createApp, migrate, seed } = require('../index.js');
const URL_ = process.env.TEST_DATABASE_URL || 'postgres://app:apppw@127.0.0.1:5432/portfolio_test';
let pool, srv, base, lastCode, cookie = '', csrf = '';
const mail = { async sendOtp(_, c) { lastCode = c; } };
const call = async (m, p, body, o = {}) => {
  const r = await fetch(base + p, { method: m, headers: { 'content-type': 'application/json', ...(o.cookie === false ? {} : { cookie }), ...(o.csrf === false ? {} : { 'x-csrf-token': csrf }), ...(o.headers || {}) }, body: body ? JSON.stringify(body) : undefined });
  let j = null; try { j = await r.json(); } catch {} return { s: r.status, j, r };
};
before(async () => {
  pool = new Pool({ connectionString: URL_ });
  await pool.query('drop schema public cascade; create schema public');
  await migrate(pool); assert.ok(await seed(pool));
  srv = createApp({ pool, mail }).listen(0); base = 'http://127.0.0.1:' + srv.address().port;
});
after(async () => { srv.close(); await pool.end(); });

test('migrations apply from empty DB and are idempotent', async () => { await migrate(pool); assert.equal((await pool.query('select count(*)::int c from schema_migrations')).rows[0].c, 4); });
test('public content: 7 seeded sections, no private fields', async () => {
  const { s, j } = await call('GET', '/api/public/content', null, { cookie: false });
  assert.equal(s, 200); assert.equal(j.sections.length, 7); assert.equal(j.settings.hero.name, 'Ravi Dhiman');
  const txt = JSON.stringify(j); assert.ok(!/published|section_id|csrf|token/.test(txt));
});
test('anonymous admin calls fail (401)', async () => {
  for (const [m, p] of [['GET', '/api/admin/sections'], ['GET', '/api/admin/settings'], ['POST', '/api/admin/sections'], ['DELETE', '/api/admin/items/1'], ['GET', '/api/admin/audit-log']])
    assert.equal((await call(m, p, m === 'POST' ? {} : null, { cookie: false, csrf: false })).s, 401, m + ' ' + p);
});
test('OTP: other email gets generic reply and no code', async () => {
  lastCode = null; const r = await call('POST', '/api/admin/auth/request-otp', { email: 'attacker@example.com' }, { cookie: false, csrf: false });
  assert.equal(r.s, 200); assert.equal(lastCode, null);
});
test('OTP: wrong code fails, attempts are limited, right code then fails after lockout', async () => {
  await call('POST', '/api/admin/auth/request-otp', { email: 'owner@example.test' }, { cookie: false, csrf: false });
  const good = lastCode, wrong = good === '000000' ? '111111' : '000000';
  for (let i = 0; i < 5; i++) assert.equal((await call('POST', '/api/admin/auth/verify-otp', { email: 'owner@example.test', code: wrong }, { cookie: false, csrf: false })).s, 401);
  assert.equal((await call('POST', '/api/admin/auth/verify-otp', { email: 'owner@example.test', code: good }, { cookie: false, csrf: false })).s, 401, 'locked after 5 attempts');
});
test('OTP: resend cooldown, then valid login, one-time use', async () => {
  await pool.query("update otp_challenges set created_at=now()-interval '5 minutes'");
  lastCode = null; await call('POST', '/api/admin/auth/request-otp', { email: 'Owner@Example.Test' }, { cookie: false, csrf: false });
  const code = lastCode; assert.match(code, /^\d{6}$/);
  const first = lastCode; await call('POST', '/api/admin/auth/request-otp', { email: 'owner@example.test' }, { cookie: false, csrf: false });
  assert.equal(lastCode, first, 'cooldown blocks a second code');
  const v = await call('POST', '/api/admin/auth/verify-otp', { email: 'owner@example.test', code }, { cookie: false, csrf: false });
  assert.equal(v.s, 200); const sc = v.r.headers.get('set-cookie'); assert.match(sc, /HttpOnly/i); assert.match(sc, /SameSite=Strict/i);
  cookie = sc.split(';')[0]; csrf = v.j.csrf;
  assert.equal((await call('POST', '/api/admin/auth/verify-otp', { email: 'owner@example.test', code }, { cookie: false, csrf: false })).s, 401, 'code reuse fails');
  const h = await pool.query('select code_hash from otp_challenges order by id desc limit 1'); assert.ok(!h.rows[0].code_hash.includes(code));
});
test('CSRF: mutation without or with wrong token is rejected; bad origin rejected', async () => {
  assert.equal((await call('POST', '/api/admin/sections', { title: 'X', street: 'X St' }, { csrf: false })).s, 403);
  assert.equal((await call('POST', '/api/admin/sections', { title: 'X', street: 'X St' }, { headers: { 'x-csrf-token': 'nope' }, csrf: false })).s, 403);
  assert.equal((await call('POST', '/api/admin/sections', { title: 'X', street: 'X St' }, { headers: { origin: 'https://evil.example' } })).s, 403);
});
let sec, item;
test('admin can add a section and an item; drafts stay private until published', async () => {
  const c = await call('POST', '/api/admin/sections', { title: 'Awards', street: 'Awards Alley', color: '#ffaa00', icon: 'bolt', layout: 'list', published: false });
  assert.equal(c.s, 201); sec = c.j;
  const i = await call('POST', '/api/admin/items', { section_id: sec.id, title: 'Test award', body: 'Body <b>x</b>', url: 'https://example.com/a' }); assert.equal(i.s, 201); item = i.j;
  let pub = (await call('GET', '/api/public/content', null, { cookie: false })).j; assert.ok(!pub.sections.find(s => s.slug.startsWith('awards')), 'draft section hidden');
  assert.equal((await call('PATCH', '/api/admin/sections/' + sec.id, { published: true })).s, 200);
  pub = (await call('GET', '/api/public/content', null, { cookie: false })).j; const s = pub.sections.find(x => x.slug === sec.slug);
  assert.ok(s && s.items[0].title === 'Test award'); assert.equal(pub.sections.length, 8);
});
test('admin can update, reorder, hide an item, and delete (cascade)', async () => {
  assert.equal((await call('PATCH', '/api/admin/items/' + item.id, { title: 'Renamed' })).j.title, 'Renamed');
  const second = (await call('POST', '/api/admin/items', { section_id: sec.id, title: 'Second' })).j;
  await call('POST', '/api/admin/items/reorder', { section_id: sec.id, ids: [second.id, item.id] });
  let list = (await call('GET', '/api/admin/sections')).j.find(s => s.id === sec.id).items; assert.deepEqual(list.map(x => x.id), [second.id, item.id]);
  await call('PATCH', '/api/admin/items/' + item.id, { published: false });
  assert.equal((await call('GET', '/api/public/content', null, { cookie: false })).j.sections.find(s => s.slug === sec.slug).items.length, 1);
  assert.equal((await call('DELETE', '/api/admin/sections/' + sec.id)).s, 200);
  assert.equal((await pool.query('select count(*)::int c from items where section_id=$1', [sec.id])).rows[0].c, 0);
  assert.equal((await call('DELETE', '/api/admin/sections/' + sec.id)).s, 404);
});
test('validation rejects bad input; SQL injection text is stored inertly', async () => {
  for (const b of [{ title: '', street: 'a' }, { title: 'a', street: 'b', color: 'red' }, { title: 'a', street: 'b', layout: 'evil' }, { title: 'a', street: 'b', icon: 'x;drop' }, { title: 'x'.repeat(61), street: 'b' }])
    assert.equal((await call('POST', '/api/admin/sections', b)).s, 400, JSON.stringify(b));
  const s0 = (await call('GET', '/api/admin/sections')).j[0];
  for (const u of ['javascript:alert(1)', 'data:text/html,x', 'ftp://x']) assert.equal((await call('POST', '/api/admin/items', { section_id: s0.id, title: 't', url: u })).s, 400, u);
  const inj = "Robert'); DROP TABLE items;--"; const r = await call('POST', '/api/admin/items', { section_id: s0.id, title: inj });
  assert.equal(r.s, 201); assert.equal((await pool.query('select title from items where id=$1', [r.j.id])).rows[0].title, inj);
  assert.equal((await call('POST', '/api/admin/items', { section_id: 99999, title: 't' })).s, 400);
});
test('project buttons: live/GitHub/docs links save, appear publicly, and are validated', async () => {
  const proj = (await call('GET', '/api/admin/sections')).j.find(s => s.layout === 'projects');
  const r = await call('POST', '/api/admin/items', { section_id: proj.id, title: 'Link test', live_url: 'https://live.example.com', repo_url: 'https://github.com/x/y', doc_url: 'https://docs.example.com/a.pdf' });
  assert.equal(r.s, 201); assert.equal(r.j.repo_url, 'https://github.com/x/y');
  const pub = (await call('GET', '/api/public/content', null, { cookie: false })).j.sections.find(s => s.layout === 'projects').items.find(i => i.title === 'Link test');
  assert.deepEqual([pub.live_url, pub.repo_url, pub.doc_url], ['https://live.example.com', 'https://github.com/x/y', 'https://docs.example.com/a.pdf']);
  for (const k of ['live_url', 'repo_url', 'doc_url']) assert.equal((await call('PATCH', '/api/admin/items/' + r.j.id, { [k]: 'javascript:alert(1)' })).s, 400, k);
  assert.equal((await call('PATCH', '/api/admin/items/' + r.j.id, { repo_url: '' })).j.repo_url, '');
  await call('DELETE', '/api/admin/items/' + r.j.id);
});
test('settings update validates and appears publicly', async () => {
  const cur = (await call('GET', '/api/admin/settings')).j; cur.hero.name = 'Ravi D.'; assert.equal((await call('PUT', '/api/admin/settings', cur)).s, 200);
  assert.equal((await call('GET', '/api/public/content', null, { cookie: false })).j.settings.hero.name, 'Ravi D.');
  cur.hero.phrases = []; assert.equal((await call('PUT', '/api/admin/settings', cur)).s, 400);
  cur.hero.phrases = ['x']; cur.socials[0].url = 'javascript:1'; assert.equal((await call('PUT', '/api/admin/settings', cur)).s, 400);
});
test('section slugs cannot collide with page element ids', async () => {
  const r = await call('POST', '/api/admin/sections', { title: 'Tour', street: 'Tour Street' }); assert.equal(r.s, 201); assert.equal(r.j.slug, 's-tour');
  await call('DELETE', '/api/admin/sections/' + r.j.id);
});
test('audit log records changes; logout revokes the session', async () => {
  const a = (await call('GET', '/api/admin/audit-log')).j; assert.ok(a.some(x => x.action === 'section.create') && a.some(x => x.action === 'login'));
  assert.equal((await call('POST', '/api/admin/auth/logout', {})).s, 200);
  assert.equal((await call('GET', '/api/admin/auth/me')).s, 401, 'old cookie no longer works');
});
test('security headers present; oversized body rejected; health ok', async () => {
  const r = await call('GET', '/api/health', null, { cookie: false }); assert.equal(r.s, 200);
  assert.equal(r.r.headers.get('x-content-type-options'), 'nosniff'); assert.match(r.r.headers.get('content-security-policy'), /frame-ancestors 'none'/);
  assert.equal((await call('POST', '/api/admin/auth/request-otp', { email: 'a'.repeat(200000) }, { cookie: false, csrf: false })).s, 413);
});
test('migration 002 moves a project row link to the Live button', async () => {
  const fs = require('fs'), path = require('path'), p2 = new Pool({ connectionString: URL_ });
  await p2.query('drop schema public cascade; create schema public');
  await p2.query(fs.readFileSync(path.join(__dirname, '../migrations/001_init.sql'), 'utf8'));
  const sec = (await p2.query("insert into sections(slug,title,street,layout) values('p','P','P St','projects'),('c','C','C St','contact') returning id")).rows;
  await p2.query("insert into items(section_id,title,url) values($1,'proj','https://a.example'),($2,'mail','mailto:a@b.co')", [sec[0].id, sec[1].id]);
  await p2.query(fs.readFileSync(path.join(__dirname, '../migrations/002_item_links.sql'), 'utf8'));
  const r = (await p2.query('select title,url,live_url from items order by id')).rows;
  assert.deepEqual(r, [{ title: 'proj', url: '', live_url: 'https://a.example' }, { title: 'mail', url: 'mailto:a@b.co', live_url: '' }]);
  await p2.query('drop schema public cascade; create schema public'); await p2.end();
  await migrate(pool); await seed(pool);   // restore for the remaining tests
});
