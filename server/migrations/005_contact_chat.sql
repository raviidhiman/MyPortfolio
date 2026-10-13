/* Contact form messages, private chat invites and chat posts */
create table contact_messages(
  id serial primary key,
  name text not null,
  email text not null,
  message text not null,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);
create table chats(
  id serial primary key,
  message_id int not null unique references contact_messages(id) on delete cascade,
  token_hash text not null unique,
  status text not null default 'open' check (status in ('open','closed')),
  admin_seen int not null default 0,
  notified_at timestamptz,
  invited_at timestamptz not null default now(),
  closed_at timestamptz
);
create table chat_posts(
  id serial primary key,
  chat_id int not null references chats(id) on delete cascade,
  sender text not null check (sender in ('visitor','admin')),
  body text not null,
  created_at timestamptz not null default now()
);
create index chat_posts_chat on chat_posts(chat_id, id);
