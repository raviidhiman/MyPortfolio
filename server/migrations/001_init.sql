create table settings(key text primary key, value jsonb not null);
create table sections(id serial primary key, slug text unique not null, title text not null, street text not null,
  color text not null default '#00e5ff', icon text not null default 'folder', layout text not null default 'list',
  position int not null default 0, published boolean not null default true, updated_at timestamptz not null default now());
create table items(id serial primary key, section_id int not null references sections(id) on delete cascade,
  title text not null, body text not null default '', details text not null default '', icon text not null default 'folder',
  url text not null default '', position int not null default 0, published boolean not null default true, updated_at timestamptz not null default now());
create index items_section_pos on items(section_id, position);
create table otp_challenges(id serial primary key, email text not null, code_hash text not null, expires_at timestamptz not null,
  attempts int not null default 0, consumed_at timestamptz, created_at timestamptz not null default now());
create table admin_sessions(token_hash text primary key, csrf text not null, expires_at timestamptz not null,
  revoked boolean not null default false, created_at timestamptz not null default now());
create table audit_events(id serial primary key, action text not null, detail text not null default '', created_at timestamptz not null default now());
