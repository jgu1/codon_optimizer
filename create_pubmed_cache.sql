drop table if exists search_terms;
create table search_terms (
  id integer primary key autoincrement,
  search_term text not null,
  num_papers integer not null,
  last_update text not null
);

drop table if exists term_paper_relation;
create table term_paper_relation(
  term_id integer not null,
  paper_id integer not null
);

drop table if exists papers;
create table papers (
  id integer primary key autoincrement,
  title text not null,
  link text not null,
  abstract text,
  keywords_str text
);

