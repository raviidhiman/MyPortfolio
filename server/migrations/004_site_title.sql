-- Tab title is now just the name. Only rewrites the old default, so a title you customised in the admin panel is never touched.
update settings set value = jsonb_set(value, '{title}', '"Ravi Dhiman"') where key = 'site' and value->>'title' in ('Ravi Dhiman — Portfolio', 'Ravi Dhiman - Portfolio');
