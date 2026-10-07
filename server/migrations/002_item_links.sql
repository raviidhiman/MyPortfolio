alter table items add column live_url text not null default '';
alter table items add column repo_url text not null default '';
alter table items add column doc_url text not null default '';
-- project rows used the single link as a whole-row link: move it to the new Live button
update items set live_url = url, url = '' where url <> '' and section_id in (select id from sections where layout = 'projects');
