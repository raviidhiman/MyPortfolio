-- Hash everything we can: the allowed e-mail is stored only as a keyed hash, never in plain text.
alter table otp_challenges add column email_h text;
update otp_challenges set email_h = encode(sha256(convert_to(email,'UTF8')),'hex');
alter table otp_challenges alter column email_h set not null;
alter table otp_challenges drop column email;
create index otp_challenges_email_h on otp_challenges(email_h, id desc);
-- Sessions: idle timeout tracking (CSRF token is now derived from the session token, not stored).
alter table admin_sessions add column last_seen timestamptz not null default now();
alter table admin_sessions alter column csrf set default '';
-- RAG: search index built only from PUBLISHED public content.
create table rag_chunks(
  id serial primary key, source text not null, section_slug text not null default '',
  title text not null, content text not null, url text not null default '',
  tsv tsvector generated always as (setweight(to_tsvector('english', coalesce(title,'')),'A') || setweight(to_tsvector('english', coalesce(content,'')),'B')) stored,
  updated_at timestamptz not null default now());
create index rag_chunks_tsv on rag_chunks using gin(tsv);
create table rag_usage(day date primary key, calls int not null default 0);
