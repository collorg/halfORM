--
-- PostgreSQL database dump
--

-- Dumped from database version 13.11 (Debian 13.11-1.pgdg110+1)
-- Dumped by pg_dump version 13.11 (Debian 13.11-1.pgdg110+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: actor; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA actor;


--
-- Name: blog; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA blog;


--
-- Name: blog.view; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA "blog.view";


--
-- Name: half_orm_meta; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA half_orm_meta;


--
-- Name: half_orm_meta.view; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA "half_orm_meta.view";


--
-- Name: meta.view; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA "meta.view";


--
-- Name: plpython3u; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpython3u WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpython3u; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpython3u IS 'PL/Python3U untrusted procedural language';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: check_database(text); Type: FUNCTION; Schema: half_orm_meta; Owner: -
--

CREATE FUNCTION half_orm_meta.check_database(old_dbid text DEFAULT NULL::text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    dbname text;
    dbid text;
BEGIN
    select current_database() into dbname;
    --XXX: use a materialized view.
    BEGIN
        select encode(hmac(dbname, pg_read_file('hop_key'), 'sha1'), 'hex') into dbid;
    EXCEPTION
        when undefined_file then
            raise NOTICE 'No hop_key file for the cluster. Will use % for dbid', dbname;
            dbid := dbname;
    END;
    if old_dbid is not null and old_dbid != dbid
    then
        raise Exception 'Not the same database!';
    end if;
    return dbid;
END;
$$;


--
-- Name: add(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.add(integer, integer) RETURNS integer
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$select $1 + $2;$_$;


--
-- Name: concat_lower_or_upper(text, text, boolean); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.concat_lower_or_upper(a text, b text, uppercase boolean DEFAULT false) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$
 SELECT CASE
        WHEN $3 THEN UPPER($1 || ' ' || $2)
        ELSE LOWER($1 || ' ' || $2)
        END;
$_$;


--
-- Name: insert_data(integer, integer); Type: PROCEDURE; Schema: public; Owner: -
--

CREATE PROCEDURE public.insert_data(a integer, b integer)
    LANGUAGE sql
    AS $$
INSERT INTO tbl VALUES (a);
INSERT INTO tbl VALUES (b);
$$;


--
-- Name: named_add(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.named_add(a integer, b integer) RETURNS integer
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$select $1 + $2;$_$;


--
-- Name: one(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.one() RETURNS integer
    LANGUAGE sql IMMUTABLE
    AS $$select 1;$$;


--
-- Name: id_person; Type: SEQUENCE; Schema: actor; Owner: -
--

CREATE SEQUENCE actor.id_person
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: person; Type: TABLE; Schema: actor; Owner: -
--

CREATE TABLE actor.person (
    id integer DEFAULT nextval('actor.id_person'::regclass) NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    birth_date date NOT NULL
);


--
-- Name: TABLE person; Type: COMMENT; Schema: actor; Owner: -
--

COMMENT ON TABLE actor.person IS 'The table actor.person contains the persons of the blogging system.
The id attribute is a serial. Just pass first_name, last_name and birth_date
to insert a new person.';


--
-- Name: id_comment; Type: SEQUENCE; Schema: blog; Owner: -
--

CREATE SEQUENCE blog.id_comment
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: comment; Type: TABLE; Schema: blog; Owner: -
--

CREATE TABLE blog.comment (
    id integer DEFAULT nextval('blog.id_comment'::regclass) NOT NULL,
    content text,
    post_id integer,
    author_id integer,
    "a = 1" text
);


--
-- Name: TABLE comment; Type: COMMENT; Schema: blog; Owner: -
--

COMMENT ON TABLE blog.comment IS 'The table blog.comment contains all the comments
made by a person on a post.';


--
-- Name: post_id; Type: SEQUENCE; Schema: blog; Owner: -
--

CREATE SEQUENCE blog.post_id
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: post; Type: TABLE; Schema: blog; Owner: -
--

CREATE TABLE blog.post (
    id integer DEFAULT nextval('blog.post_id'::regclass) NOT NULL,
    title text,
    content text,
    author_first_name text,
    author_last_name text,
    author_birth_date date,
    data jsonb
);


--
-- Name: TABLE post; Type: COMMENT; Schema: blog; Owner: -
--

COMMENT ON TABLE blog.post IS 'The table blog.post contains all the post
made by a person in the blogging system.';


--
-- Name: event; Type: TABLE; Schema: blog; Owner: -
--

CREATE TABLE blog.event (
    id integer DEFAULT nextval('blog.post_id'::regclass),
    begin timestamp(0) without time zone,
    "end" timestamp(0) without time zone,
    location text
)
INHERITS (blog.post);


--
-- Name: TABLE event; Type: COMMENT; Schema: blog; Owner: -
--

COMMENT ON TABLE blog.event IS 'The table blog.event contains all the events
of the blogging system. It inherits blog.post.
It''s just here to illustrate the inheriance in half_orm';


--
-- Name: post_comment; Type: VIEW; Schema: blog.view; Owner: -
--

CREATE VIEW "blog.view".post_comment AS
 SELECT post.title AS post_title,
    auth_p.id AS author_post_id,
    auth_p.first_name AS author_post_first_name,
    auth_p.last_name AS author_post_last_name,
    comment.id AS comment_id,
    comment.content AS comment_content,
    comment.post_id,
    auth_c.id AS author_comment_id,
    auth_c.first_name AS author_comment_first_name,
    auth_c.last_name AS author_comment_last_name
   FROM (((blog.post
     JOIN actor.person auth_p ON (((post.author_first_name = auth_p.first_name) AND (post.author_last_name = auth_p.last_name) AND (post.author_birth_date = auth_p.birth_date))))
     LEFT JOIN blog.comment ON ((post.id = comment.post_id)))
     LEFT JOIN actor.person auth_c ON ((comment.author_id = auth_c.id)));


--
-- Name: VIEW post_comment; Type: COMMENT; Schema: blog.view; Owner: -
--

COMMENT ON VIEW "blog.view".post_comment IS 'This view joins:
- comment,
- author of the comment,
- post,
- author of the post.';


--
-- Name: database; Type: TABLE; Schema: half_orm_meta; Owner: -
--

CREATE TABLE half_orm_meta.database (
    id text NOT NULL,
    name text NOT NULL,
    description text
);


--
-- Name: TABLE database; Type: COMMENT; Schema: half_orm_meta; Owner: -
--

COMMENT ON TABLE half_orm_meta.database IS '
id identifies the database in the cluster. It uses the key
in hop_key.
';


--
-- Name: hop_release; Type: TABLE; Schema: half_orm_meta; Owner: -
--

CREATE TABLE half_orm_meta.hop_release (
    major integer NOT NULL,
    minor integer NOT NULL,
    patch integer NOT NULL,
    pre_release text DEFAULT ''::text NOT NULL,
    pre_release_num text DEFAULT ''::text NOT NULL,
    date date DEFAULT CURRENT_DATE,
    "time" time(0) with time zone DEFAULT CURRENT_TIME,
    changelog text,
    commit text,
    dbid text,
    hop_release text,
    CONSTRAINT hop_release_major_check CHECK ((major >= 0)),
    CONSTRAINT hop_release_minor_check CHECK ((minor >= 0)),
    CONSTRAINT hop_release_patch_check CHECK ((patch >= 0)),
    CONSTRAINT hop_release_pre_release_check CHECK ((pre_release = ANY (ARRAY['alpha'::text, 'beta'::text, 'rc'::text, ''::text]))),
    CONSTRAINT hop_release_pre_release_num_check CHECK (((pre_release_num = ''::text) OR (pre_release_num ~ '^\d+$'::text)))
);


--
-- Name: hop_release_issue; Type: TABLE; Schema: half_orm_meta; Owner: -
--

CREATE TABLE half_orm_meta.hop_release_issue (
    num integer NOT NULL,
    issue_release integer DEFAULT 0 NOT NULL,
    release_major integer NOT NULL,
    release_minor integer NOT NULL,
    release_patch integer NOT NULL,
    release_pre_release text NOT NULL,
    release_pre_release_num text NOT NULL,
    changelog text,
    CONSTRAINT hop_release_issue_num_check CHECK ((num >= 0))
);


--
-- Name: hop_last_release; Type: VIEW; Schema: half_orm_meta.view; Owner: -
--

CREATE VIEW "half_orm_meta.view".hop_last_release AS
 SELECT hop_release.major,
    hop_release.minor,
    hop_release.patch,
    hop_release.pre_release,
    hop_release.pre_release_num,
    hop_release.date,
    hop_release."time",
    hop_release.changelog,
    hop_release.commit
   FROM half_orm_meta.hop_release
  ORDER BY hop_release.major DESC, hop_release.minor DESC, hop_release.patch DESC, hop_release.pre_release DESC, hop_release.pre_release_num DESC
 LIMIT 1;


--
-- Name: hop_penultimate_release; Type: VIEW; Schema: half_orm_meta.view; Owner: -
--

CREATE VIEW "half_orm_meta.view".hop_penultimate_release AS
 SELECT penultimate.major,
    penultimate.minor,
    penultimate.patch
   FROM ( SELECT hop_release.major,
            hop_release.minor,
            hop_release.patch
           FROM half_orm_meta.hop_release
          ORDER BY hop_release.major DESC, hop_release.minor DESC, hop_release.patch DESC
         LIMIT 2) penultimate
  ORDER BY penultimate.major, penultimate.minor, penultimate.patch
 LIMIT 1;


--
-- Name: person person_first_name_key; Type: CONSTRAINT; Schema: actor; Owner: -
--

ALTER TABLE ONLY actor.person
    ADD CONSTRAINT person_first_name_key UNIQUE (first_name);


--
-- Name: person person_id_key; Type: CONSTRAINT; Schema: actor; Owner: -
--

ALTER TABLE ONLY actor.person
    ADD CONSTRAINT person_id_key UNIQUE (id);


--
-- Name: person person_pkey; Type: CONSTRAINT; Schema: actor; Owner: -
--

ALTER TABLE ONLY actor.person
    ADD CONSTRAINT person_pkey PRIMARY KEY (first_name, last_name, birth_date);


--
-- Name: comment comment_pkey; Type: CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.comment
    ADD CONSTRAINT comment_pkey PRIMARY KEY (id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (id);


--
-- Name: post post_pkey; Type: CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.post
    ADD CONSTRAINT post_pkey PRIMARY KEY (id);


--
-- Name: post post_title_content_key; Type: CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.post
    ADD CONSTRAINT post_title_content_key UNIQUE (title, content);


--
-- Name: database database_pkey; Type: CONSTRAINT; Schema: half_orm_meta; Owner: -
--

ALTER TABLE ONLY half_orm_meta.database
    ADD CONSTRAINT database_pkey PRIMARY KEY (id);


--
-- Name: hop_release_issue hop_release_issue_pkey; Type: CONSTRAINT; Schema: half_orm_meta; Owner: -
--

ALTER TABLE ONLY half_orm_meta.hop_release_issue
    ADD CONSTRAINT hop_release_issue_pkey PRIMARY KEY (num, issue_release);


--
-- Name: hop_release hop_release_pkey; Type: CONSTRAINT; Schema: half_orm_meta; Owner: -
--

ALTER TABLE ONLY half_orm_meta.hop_release
    ADD CONSTRAINT hop_release_pkey PRIMARY KEY (major, minor, patch, pre_release, pre_release_num);


--
-- Name: post author; Type: FK CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.post
    ADD CONSTRAINT author FOREIGN KEY (author_first_name, author_last_name, author_birth_date) REFERENCES actor.person(first_name, last_name, birth_date) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: comment author; Type: FK CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.comment
    ADD CONSTRAINT author FOREIGN KEY (author_id) REFERENCES actor.person(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: event author; Type: FK CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.event
    ADD CONSTRAINT author FOREIGN KEY (author_first_name, author_last_name, author_birth_date) REFERENCES actor.person(first_name, last_name, birth_date) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: comment post; Type: FK CONSTRAINT; Schema: blog; Owner: -
--

ALTER TABLE ONLY blog.comment
    ADD CONSTRAINT post FOREIGN KEY (post_id) REFERENCES blog.post(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: hop_release hop_release_dbid_fkey; Type: FK CONSTRAINT; Schema: half_orm_meta; Owner: -
--

ALTER TABLE ONLY half_orm_meta.hop_release
    ADD CONSTRAINT hop_release_dbid_fkey FOREIGN KEY (dbid) REFERENCES half_orm_meta.database(id) ON UPDATE CASCADE;


--
-- Name: hop_release_issue hop_release_issue_release_major_release_minor_release_patc_fkey; Type: FK CONSTRAINT; Schema: half_orm_meta; Owner: -
--

ALTER TABLE ONLY half_orm_meta.hop_release_issue
    ADD CONSTRAINT hop_release_issue_release_major_release_minor_release_patc_fkey FOREIGN KEY (release_major, release_minor, release_patch, release_pre_release, release_pre_release_num) REFERENCES half_orm_meta.hop_release(major, minor, patch, pre_release, pre_release_num);


--
-- PostgreSQL database dump complete
--

