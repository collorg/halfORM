create user halftest password 'halftest';
create database halftest owner halftest;
comment on database halftest is
'Database used to test half_orm. Sort of blogging database';

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
comment on table actor.person is
'The table actor.person contains the persons of the blogging system.
The id attribute is a serial. Just pass first_name, last_name and birth_date
to insert a new person.';
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
comment on table blog.post is
'The table blog.post contains all the post
made by a person in the blogging system.';

create table blog.event(
    id int default nextval('blog.post_id') unique not null,
    "begin" timestamp(0),
    "end" timestamp(0),
    location text,
    primary key(id)
) inherits(blog.post);
alter table blog.event add constraint "author"
    foreign key(author_first_name, author_last_name, author_birth_date)
    references actor.person(first_name, last_name, birth_date)
	on update cascade on delete cascade;
grant all on table blog.event to halftest;
comment on table blog.event is
'The table blog.event contains all the events
of the blogging system. It inherits blog.post.
It''s just here to illustrate the inheriance in half_orm';

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
comment on table blog.comment is
'The table blog.comment contains all the comments
made by a person on a post.';

create schema "blog.view"
grant all on schema "blog.view" to halftest;

create view "blog.view".post_comment as
select
    post.title as post_title,
    auth_p.id as author_post_id,
    auth_p.first_name as author_post_first_name,
    auth_p.last_name as author_post_last_name,
    comment.id as comment_id,
    comment.content as comment_content,
    comment.post_id as post_id,
    auth_c.id as author_comment_id,
    auth_c.first_name as author_comment_first_name,
    auth_c.last_name as author_comment_last_name
from
    blog.post
    join actor.person as auth_p on
    post.author_first_name = auth_p.first_name and
    post.author_last_name = auth_p.last_name and
    post.author_birth_date = auth_p.birth_date
    left join blog.comment on
    post.id = comment.post_id
    left join actor.person as auth_c on
    comment.author_id = auth_c.id;

grant all on "blog.view".post_comment to halftest;
comment on view "blog.view".post_comment is
'This view joins:
- comment,
- author of the comment,
- post,
- author of the post.';
