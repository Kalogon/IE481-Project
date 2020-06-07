create table if not exists user (
  user_id integer primary key autoincrement,
  username string not null,
  email string not null,
  pw_hash string not null
);
