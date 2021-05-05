create schema "meta.view";
create schema meta;
create table meta.release (
    major int check (major >= 0),
    minor int check (minor >= 0),
    patch int check (patch >= 0),
    pre_release text check (pre_release in ('alpha', 'beta', 'rc', '')) default '',
    pre_release_num text check (
        pre_release_num = '' or pre_release_num ~ '^\d+$') default '',
    "date" date default current_date,
    "time" time(0) with time zone default current_time,
    changelog text,
    commit text,
    primary key(major, minor, patch, pre_release, pre_release_num)
);
