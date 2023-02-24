--
-- PostgreSQL database dump
--

-- Dumped from database version 13.10 (Debian 13.10-1.pgdg110+1)
-- Dumped by pg_dump version 13.10 (Debian 13.10-1.pgdg110+1)

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
 WITH sub AS (
         SELECT hop_release.major,
            hop_release.minor,
            hop_release.patch,
            row_number() OVER (ORDER BY hop_release.major DESC, hop_release.minor DESC, hop_release.patch DESC) AS rn
           FROM half_orm_meta.hop_release
        )
 SELECT sub.major,
    sub.minor,
    sub.patch
   FROM sub
  WHERE (sub.rn = 2);


--
-- Data for Name: person; Type: TABLE DATA; Schema: actor; Owner: -
--

COPY actor.person (id, first_name, last_name, birth_date) FROM stdin;
6768	ba	ba	2023-02-15
6769	bb	bb	2023-02-15
6770	bc	bc	2023-02-15
6771	bd	bd	2023-02-15
6772	be	be	2023-02-15
6773	bf	bf	2023-02-15
6774	bg	bg	2023-02-15
6775	bh	bh	2023-02-15
6776	bi	bi	2023-02-15
6777	bj	bj	2023-02-15
6778	ca	ca	2023-02-15
6779	cb	cb	2023-02-15
6780	cc	cc	2023-02-15
6781	cd	cd	2023-02-15
6782	ce	ce	2023-02-15
6783	cf	cf	2023-02-15
6784	cg	cg	2023-02-15
6785	ch	ch	2023-02-15
6786	ci	ci	2023-02-15
6787	cj	cj	2023-02-15
6788	da	da	2023-02-15
6789	db	db	2023-02-15
6790	dc	dc	2023-02-15
6791	dd	dd	2023-02-15
6792	de	de	2023-02-15
6793	df	df	2023-02-15
6794	dg	dg	2023-02-15
6795	dh	dh	2023-02-15
6796	di	di	2023-02-15
6797	dj	dj	2023-02-15
6798	ea	ea	2023-02-15
6799	eb	eb	2023-02-15
6800	ec	ec	2023-02-15
6801	ed	ed	2023-02-15
6802	ee	ee	2023-02-15
6803	ef	ef	2023-02-15
6804	eg	eg	2023-02-15
6805	eh	eh	2023-02-15
6806	ei	ei	2023-02-15
6807	ej	ej	2023-02-15
6808	fa	fa	2023-02-15
6809	fb	fb	2023-02-15
6810	fc	fc	2023-02-15
6811	fd	fd	2023-02-15
6812	fe	fe	2023-02-15
6813	ff	ff	2023-02-15
6814	fg	fg	2023-02-15
6815	fh	fh	2023-02-15
6816	fi	fi	2023-02-15
6817	fj	fj	2023-02-15
6758	aa	aa	2023-02-15
6759	ab	ab	2023-02-15
6760	ac	ac	2023-02-15
6761	ad	ad	2023-02-15
6762	ae	ae	2023-02-15
6763	af	af	2023-02-15
6764	ag	ag	2023-02-15
6765	ah	ah	2023-02-15
6766	ai	ai	2023-02-15
6767	aj	aj	2023-02-15
\.


--
-- Data for Name: comment; Type: TABLE DATA; Schema: blog; Owner: -
--

COPY blog.comment (id, content, post_id, author_id, "a = 1") FROM stdin;
\.


--
-- Data for Name: event; Type: TABLE DATA; Schema: blog; Owner: -
--

COPY blog.event (id, title, content, author_first_name, author_last_name, author_birth_date, begin, "end", location, data) FROM stdin;
\.


--
-- Data for Name: post; Type: TABLE DATA; Schema: blog; Owner: -
--

COPY blog.post (id, title, content, author_first_name, author_last_name, author_birth_date, data) FROM stdin;
\.


--
-- Data for Name: hop_release; Type: TABLE DATA; Schema: half_orm_meta; Owner: -
--

COPY half_orm_meta.hop_release (major, minor, patch, pre_release, pre_release_num, date, "time", changelog, commit) FROM stdin;
0	0	0			2023-01-05	09:03:55+01	Initial release	\N
0	0	1			2023-01-24	14:20:25+01		\N
\.


--
-- Data for Name: hop_release_issue; Type: TABLE DATA; Schema: half_orm_meta; Owner: -
--

COPY half_orm_meta.hop_release_issue (num, issue_release, release_major, release_minor, release_patch, release_pre_release, release_pre_release_num, changelog) FROM stdin;
\.


--
-- Name: id_person; Type: SEQUENCE SET; Schema: actor; Owner: -
--

SELECT pg_catalog.setval('actor.id_person', 7188, true);


--
-- Name: id_comment; Type: SEQUENCE SET; Schema: blog; Owner: -
--

SELECT pg_catalog.setval('blog.id_comment', 21099, true);


--
-- Name: post_id; Type: SEQUENCE SET; Schema: blog; Owner: -
--

SELECT pg_catalog.setval('blog.post_id', 15255, true);


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
-- Name: hop_release_issue hop_release_issue_release_major_release_minor_release_patc_fkey; Type: FK CONSTRAINT; Schema: half_orm_meta; Owner: -
--

ALTER TABLE ONLY half_orm_meta.hop_release_issue
    ADD CONSTRAINT hop_release_issue_release_major_release_minor_release_patc_fkey FOREIGN KEY (release_major, release_minor, release_patch, release_pre_release, release_pre_release_num) REFERENCES half_orm_meta.hop_release(major, minor, patch, pre_release, pre_release_num);


--
-- PostgreSQL database dump complete
--

