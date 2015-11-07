create table e(
    id text primary key,
    b_id text
);

create table d(
    id text primary key,
    e_id text,
    foreign key(e_id) references e(id),
    a_id text
);
create table c(
    id text primary key,
    d_id text,
    foreign key(d_id) references d(id)
);
create table b(
    id text primary key,
    c_id text,
    foreign key(c_id) references c(id)
);
create table a(
    id text primary key,
    b_id text,
    foreign key(b_id) references b(id),
    c_id text,
    foreign key(c_id) references c(id)
);
alter table d add constraint d_a_id_fkey
    foreign key(a_id) references a(id);
alter table e add constraint e_b_id_fkey
    foreign key(b_id) references b(id);
