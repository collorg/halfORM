create user halftest password 'halftest';
create database halftest owner halftest;

\c halftest

create schema actor;
grant all on schema actor to halftest;
create sequence actor.id_person;
create table actor.person(
    id int default nextval('actor.id_person') unique not null,
    first_name text,
    last_name text,
    birth_date date,
    primary key(first_name, last_name, birth_date)
);
grant all on table actor.person to halftest;
grant all on table actor.id_person to halftest;

create schema blog;
grant all on schema blog to halftest;
create sequence blog.post_id;
create table blog.post(
    id int default nextval('blog.post_id') unique not null,
    title text,
    content text,
    author_first_name text,
    author_last_name text,
    author_birth_date date,
    primary key(id)
);
alter table blog.post add constraint "author"
    foreign key(author_first_name, author_last_name, author_birth_date)
    references actor.person(first_name, last_name, birth_date)
	on update cascade on delete cascade;
grant all on table blog.post to halftest;
grant all on table blog.post_id to halftest;

create sequence blog.id_comment;
create table blog.comment(
    id int default nextval('blog.id_comment') unique not null,
    content text,
    post_id int,
    author_id int,
    primary key(id)
);
alter table blog.comment add constraint "author"
    foreign key(author_id) references actor.person(id)
	on update cascade on delete cascade;
alter table blog.comment add constraint "post"
    foreign key(post_id)
    references blog.post
	on update cascade on delete cascade;
grant all on table blog.comment to halftest;
grant all on table blog.id_comment to halftest;

create schema "blog.view"
grant all on schema "blog.view" to halftest;

create view "blog.view".post_comment as
select
    comment.id as comment_id,
    comment.content as comment_content,
    comment.post_id as post_id,
    auth_c.id as author_comment_id,
    auth_c.first_name as author_comment_first_name,
    auth_c.last_name as author_comment_last_name
from
    blog.comment
    join actor.person as auth_c on
    comment.author_id = auth_c.id;
grant all on "blog.view".post_comment to halftest;
