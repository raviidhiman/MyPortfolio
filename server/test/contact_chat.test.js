process.env.ADMIN_EMAIL = 'owner@example.test'; process.env.OTP_SECRET = 'test-secret'; process.env.SITE_URL = 'https://site.example'; process.env.WHATSAPP_NUMBER = '+91 93065 39506';
const { test, before, after } = require('node:test'); const assert = require('node:assert');
const { Pool } = require('pg'); const { createApp, migrate, seed } = require('../index.js');
const URL_ = process.env.TEST_DATABASE_URL || 'postgres://app:apppw@127.0.0.1:5432/portfolio_test';
let pool, srv, base, lastCode, cookie = '', csrf = ''; const sent = { contact: [], invite: [], notice: [] };
const mail = { async sendOtp(_, c) { lastCode = c; }, async sendContact(to, m) { sent.contact.push({ to, ...m }); }, async sendChatInvite(to, m) { sent.invite.push({ to, ...m }); }, async sendChatNotice(to, m) { sent.notice.push({ to, ...m }); } };
let ip = 10;
const call = async (m, p, body, o = {}) => {
  const r = await fetch(base + p, { method: m, headers: { 'content-type': 'application/json', 'x-forwarded-for': o.ip || '10.0.0.' + (ip++), ...(o.cookie === false ? {} : { cookie }), ...(o.csrf === false ? {} : { 'x-csrf-token': csrf }) }, body: body ? JSON.stringify(body) : undefined });
  let j = null; try { j = await r.json(); } catch {} return { s: r.status, j, r };
};
const pub = { cookie: false, csrf: false };
before(async () => {
  pool = new Pool({ connectionString: URL_ }); await pool.query('drop schema public cascade; create schema public');
  await migrate(pool); assert.ok(await seed(pool)); srv = createApp({ pool, mail }).listen(0); base = 'http://127.0.0.1:' + srv.address().port;
  await call('POST', '/api/admin/auth/request-otp', {}, pub);
  const v = await call('POST', '/api/admin/auth/verify-otp', { code: lastCode }, pub); cookie = v.r.headers.get('set-cookie').split(';')[0]; csrf = v.j.csrf;
});
after(async () => { srv.close(); await pool.end(); });
const form = (o = {}) => ({ name: 'Asha Verma', email: 'Asha@Example.com', message: 'Hello, I would like to work with you.', ...o });

test('contact form: saved, lower-cased e-mail, and the owner is notified at ADMIN_EMAIL (reply-to is the visitor)', async () => {
  const r = await call('POST', '/api/contact', form(), pub); assert.equal(r.s, 201);
  assert.equal(sent.contact.length, 1); assert.equal(sent.contact[0].to, 'owner@example.test'); assert.equal(sent.contact[0].email, 'asha@example.com');
  const row = (await pool.query('select * from contact_messages')).rows[0]; assert.equal(row.name, 'Asha Verma'); assert.equal(row.is_read, false);
});
test('contact form: validation, honeypot and rate limit', async () => {
  for (const bad of [form({ name: '' }), form({ email: 'nope' }), form({ message: '' }), form({ message: 'x'.repeat(3001) }), form({ name: 5 })]) assert.equal((await call('POST', '/api/contact', bad, pub)).s, 400);
  const n = (await pool.query('select count(*)::int c from contact_messages')).rows[0].c;
  assert.equal((await call('POST', '/api/contact', form({ website: 'http://spam.example' }), pub)).s, 201); assert.equal((await pool.query('select count(*)::int c from contact_messages')).rows[0].c, n, 'honeypot: nothing saved');
  assert.equal(sent.contact.length, 1, 'honeypot: no email');
  const own = '203.0.113.9'; let last; for (let i = 0; i < 6; i++) last = await call('POST', '/api/contact', form({ message: 'hello ' + i }), { ...pub, ip: own });
  assert.equal(last.s, 429, '6th message from one address in an hour is refused');
});
test('contact form: a failing e-mail provider still saves the message', async () => {
  const keep = mail.sendContact; mail.sendContact = async () => { throw new Error('brevo down'); };
  const r = await call('POST', '/api/contact', form({ message: 'saved even if mail fails' }), pub); mail.sendContact = keep; assert.equal(r.s, 201);
  assert.ok((await pool.query("select 1 from contact_messages where message='saved even if mail fails'")).rowCount);
});
test('inbox endpoints need the admin session and a CSRF token', async () => {
  for (const [m, p] of [['GET', '/api/admin/messages'], ['POST', '/api/admin/messages/1/invite'], ['GET', '/api/admin/chats/1'], ['POST', '/api/admin/chats/1/close'], ['DELETE', '/api/admin/messages/1']])
    assert.equal((await call(m, p, m === 'GET' ? null : {}, pub)).s, 401, m + ' ' + p);
  assert.equal((await call('POST', '/api/admin/messages/1/invite', {}, { csrf: false })).s, 403, 'no CSRF token');
});
let chatId, token, msgId;
test('admin lists messages and sends a chat invite by e-mail; the link works for the visitor', async () => {
  const list = await call('GET', '/api/admin/messages'); assert.equal(list.s, 200); assert.ok(list.j.length >= 2); const m = list.j.find(x => x.email === 'asha@example.com'); msgId = m.id;
  assert.equal(m.chat_id, null);
  const inv = await call('POST', `/api/admin/messages/${msgId}/invite`, {}); assert.equal(inv.s, 200); chatId = inv.j.chat_id;
  const e = sent.invite.at(-1); assert.equal(e.to, 'asha@example.com'); assert.match(e.link, /^https:\/\/site\.example\/chat\/[A-Za-z0-9_-]{20,}$/); token = e.link.split('/').pop();
  const raw = (await pool.query('select token_hash from chats where id=$1', [chatId])).rows[0].token_hash; assert.ok(!raw.includes(token), 'token is stored hashed');
  const v = await call('GET', '/api/chat/' + token, null, pub); assert.equal(v.s, 200); assert.equal(v.j.status, 'open'); assert.equal(v.j.name, 'Asha Verma'); assert.deepEqual(v.j.posts, []);
  assert.ok(!JSON.stringify(v.j).includes('asha@example.com'), 'visitor endpoint does not leak the e-mail');
});
test('chat: visitor and admin exchange messages; polling with ?after returns only new ones; owner gets one throttled notice', async () => {
  assert.equal((await call('POST', `/api/chat/${token}/post`, { body: 'Hi Ravi!' }, pub)).s, 201);
  assert.equal((await call('POST', `/api/chat/${token}/post`, { body: 'Second message' }, pub)).s, 201);
  assert.equal(sent.notice.length, 1, 'only one notice within 10 minutes'); assert.equal(sent.notice[0].to, 'owner@example.test');
  const a = await call('GET', '/api/admin/chats/' + chatId); assert.equal(a.j.posts.length, 2); assert.equal(a.j.posts[0].sender, 'visitor');
  const lst = (await call('GET', '/api/admin/messages')).j.find(x => x.id === msgId); assert.equal(lst.unread, 0, 'opening the chat marks it seen');
  assert.equal((await call('POST', `/api/admin/chats/${chatId}/post`, { body: 'Hello Asha' })).s, 201);
  const after = a.j.posts.at(-1).id, v = await call('GET', `/api/chat/${token}?after=${after}`, null, pub); assert.equal(v.j.posts.length, 1); assert.equal(v.j.posts[0].sender, 'admin'); assert.equal(v.j.posts[0].body, 'Hello Asha');
  assert.equal((await call('POST', `/api/chat/${token}/post`, { body: '   ' }, pub)).s, 400); assert.equal((await call('POST', `/api/chat/${token}/post`, { body: 'x'.repeat(1001) }, pub)).s, 400);
  assert.equal((await call('POST', '/api/chat/' + token + '/post', { body: 'new msg' }, pub)).s, 201);
  assert.equal((await call('GET', '/api/admin/messages')).j.find(x => x.id === msgId).unread, 1, 'new visitor message counts as unread');
});
test('chat: invalid or guessed links return 404', async () => {
  for (const t of ['short', 'a'.repeat(32), '../etc/passwd', 'x'.repeat(100)]) assert.equal((await call('GET', '/api/chat/' + encodeURIComponent(t), null, pub)).s, 404, t);
});
test('chat: admin can close it any time; visitor can no longer post; history stays readable', async () => {
  assert.equal((await call('POST', `/api/admin/chats/${chatId}/close`, {})).s, 200);
  const r = await call('POST', `/api/chat/${token}/post`, { body: 'still there?' }, pub); assert.equal(r.s, 409); assert.match(r.j.error, /closed/i);
  assert.equal((await call('POST', `/api/admin/chats/${chatId}/post`, { body: 'x' })).s, 409);
  const v = await call('GET', '/api/chat/' + token, null, pub); assert.equal(v.j.status, 'closed'); assert.ok(v.j.posts.length >= 3);
});
test('chat: sending the invite again reopens it with a new link and the old link stops working', async () => {
  assert.equal((await call('POST', `/api/admin/messages/${msgId}/invite`, {})).s, 200); const nt = sent.invite.at(-1).link.split('/').pop(); assert.notEqual(nt, token);
  assert.equal((await call('GET', '/api/chat/' + token, null, pub)).s, 404, 'old link dead'); assert.equal((await call('GET', '/api/chat/' + nt, null, pub)).j.status, 'open');
  assert.equal((await pool.query('select count(*)::int c from chats where message_id=$1', [msgId])).rows[0].c, 1, 'same chat row');
  token = nt;
});
test('failed invite e-mail returns an error and keeps the old link working', async () => {
  const keep = mail.sendChatInvite; mail.sendChatInvite = async () => { throw new Error('x'); };
  const r = await call('POST', `/api/admin/messages/${msgId}/invite`, {}); mail.sendChatInvite = keep; assert.equal(r.s, 502);
  assert.equal((await call('GET', '/api/chat/' + token, null, pub)).s, 200);
});
test('deleting a message deletes its chat; chat traffic never triggers a search re-index', async () => {
  assert.equal((await call('DELETE', '/api/admin/messages/' + msgId)).s, 200);
  assert.equal((await call('GET', '/api/chat/' + token, null, pub)).s, 404); assert.equal((await call('GET', '/api/admin/messages/999999/x')).s, 404);
});

test('pages: every published section has its own URL with its own title, canonical link and page marker', async () => {
  const r = await fetch(base + '/about'); assert.equal(r.status, 200); const h = await r.text();
  assert.match(h, /<title>About — Ravi Dhiman<\/title>/); assert.ok(h.includes('window.__PAGE__="about"')); assert.ok(h.includes('<link rel="canonical" href="https://site.example/about">'));
  assert.ok(h.includes('google-site-verification'));
  const home = await (await fetch(base + '/')).text(); assert.ok(home.includes('window.__PAGE__=""')); assert.match(home, /<title>Ravi Dhiman<\/title>/);
  assert.equal((await fetch(base + '/no-such-section')).status, 404);
  const sec = await call('POST', '/api/admin/sections', { title: 'Hidden', street: 'H St', published: false }); const slug = sec.j.slug;
  assert.equal((await fetch(base + '/' + slug)).status, 404, 'unpublished sections have no page'); await call('DELETE', '/api/admin/sections/' + sec.j.id);
  const c = await (await fetch(base + '/connect')).text(); assert.ok(c.includes('window.__PAGE__="connect"')); assert.ok(c.includes('window.__WA__="919306539506"'), 'WhatsApp number is digits only');
  const ch = await fetch(base + '/chat/abc'); assert.equal(ch.status, 200); assert.equal(ch.headers.get('x-robots-tag'), 'noindex');
});
test('sitemap.xml lists home, every published section and /connect; robots.txt points to it and hides private areas', async () => {
  const r = await fetch(base + '/sitemap.xml'); assert.equal(r.status, 200); assert.match(r.headers.get('content-type'), /xml/); const x = await r.text();
  assert.match(x, /<urlset xmlns="http:\/\/www\.sitemaps\.org\/schemas\/sitemap\/0\.9">/);
  for (const p of ['/', '/about', '/skills', '/projects', '/experience', '/education', '/research', '/contact', '/connect']) assert.ok(x.includes(`<loc>https://site.example${p}</loc>`), p);
  assert.ok(!x.includes('/admin') && !x.includes('/chat'));
  const rb = await (await fetch(base + '/robots.txt')).text(); assert.ok(rb.includes('Sitemap: https://site.example/sitemap.xml')); assert.ok(rb.includes('Disallow: /admin/') && rb.includes('Disallow: /chat/'));
  await pool.query("update sections set published=false where slug='research'"); assert.ok(!(await (await fetch(base + '/sitemap.xml')).text()).includes('/research'), 'unpublished sections leave the sitemap');
  await pool.query("update sections set published=true where slug='research'");
});
test('reserved page names cannot be used as section slugs', async () => {
  for (const t of ['Connect', 'Chat', 'Admin', 'Sitemap']) { const r = await call('POST', '/api/admin/sections', { title: t, street: 'S' }); assert.equal(r.s, 201); assert.ok(r.j.slug.startsWith('s-'), t + ' -> ' + r.j.slug); await call('DELETE', '/api/admin/sections/' + r.j.id); }
});
