--
-- PostgreSQL database dump
--

-- Dumped from database version 13.3 (Debian 13.3-1.pgdg100+1)
-- Dumped by pg_dump version 13.3 (Debian 13.3-1.pgdg100+1)

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
-- Name: actor; Type: SCHEMA; Schema: -; Owner: halftest
--

CREATE SCHEMA actor;


ALTER SCHEMA actor OWNER TO halftest;

--
-- Name: blog; Type: SCHEMA; Schema: -; Owner: halftest
--

CREATE SCHEMA blog;


ALTER SCHEMA blog OWNER TO halftest;

--
-- Name: blog.view; Type: SCHEMA; Schema: -; Owner: halftest
--

CREATE SCHEMA "blog.view";


ALTER SCHEMA "blog.view" OWNER TO halftest;

--
-- Name: meta.view; Type: SCHEMA; Schema: -; Owner: halftest
--

CREATE SCHEMA "meta.view";


ALTER SCHEMA "meta.view" OWNER TO halftest;

--
-- Name: plpython3u; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpython3u WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpython3u; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpython3u IS 'PL/Python3U untrusted procedural language';


--
-- Name: id_person; Type: SEQUENCE; Schema: actor; Owner: halftest
--

CREATE SEQUENCE actor.id_person
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE actor.id_person OWNER TO halftest;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: person; Type: TABLE; Schema: actor; Owner: halftest
--

CREATE TABLE actor.person (
    id integer DEFAULT nextval('actor.id_person'::regclass) NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    birth_date date NOT NULL
);


ALTER TABLE actor.person OWNER TO halftest;

--
-- Name: TABLE person; Type: COMMENT; Schema: actor; Owner: halftest
--

COMMENT ON TABLE actor.person IS 'The table actor.person contains the persons of the blogging system.
The id attribute is a serial. Just pass first_name, last_name and birth_date
to insert a new person.';


--
-- Name: id_comment; Type: SEQUENCE; Schema: blog; Owner: halftest
--

CREATE SEQUENCE blog.id_comment
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE blog.id_comment OWNER TO halftest;

--
-- Name: comment; Type: TABLE; Schema: blog; Owner: halftest
--

CREATE TABLE blog.comment (
    id integer DEFAULT nextval('blog.id_comment'::regclass) NOT NULL,
    content text,
    post_id integer,
    author_id integer,
    "a = 1" text
);


ALTER TABLE blog.comment OWNER TO halftest;

--
-- Name: TABLE comment; Type: COMMENT; Schema: blog; Owner: halftest
--

COMMENT ON TABLE blog.comment IS 'The table blog.comment contains all the comments
made by a person on a post.';


--
-- Name: post_id; Type: SEQUENCE; Schema: blog; Owner: halftest
--

CREATE SEQUENCE blog.post_id
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE blog.post_id OWNER TO halftest;

--
-- Name: post; Type: TABLE; Schema: blog; Owner: halftest
--

CREATE TABLE blog.post (
    id integer DEFAULT nextval('blog.post_id'::regclass) NOT NULL,
    title text,
    content text,
    author_first_name text,
    author_last_name text,
    author_birth_date date
);


ALTER TABLE blog.post OWNER TO halftest;

--
-- Name: TABLE post; Type: COMMENT; Schema: blog; Owner: halftest
--

COMMENT ON TABLE blog.post IS 'The table blog.post contains all the post
made by a person in the blogging system.';


--
-- Name: event; Type: TABLE; Schema: blog; Owner: halftest
--

CREATE TABLE blog.event (
    id integer DEFAULT nextval('blog.post_id'::regclass),
    begin timestamp(0) without time zone,
    "end" timestamp(0) without time zone,
    location text
)
INHERITS (blog.post);


ALTER TABLE blog.event OWNER TO halftest;

--
-- Name: TABLE event; Type: COMMENT; Schema: blog; Owner: halftest
--

COMMENT ON TABLE blog.event IS 'The table blog.event contains all the events
of the blogging system. It inherits blog.post.
It''s just here to illustrate the inheriance in half_orm';


--
-- Name: post_comment; Type: VIEW; Schema: blog.view; Owner: halftest
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


ALTER TABLE "blog.view".post_comment OWNER TO halftest;

--
-- Name: VIEW post_comment; Type: COMMENT; Schema: blog.view; Owner: halftest
--

COMMENT ON VIEW "blog.view".post_comment IS 'This view joins:
- comment,
- author of the comment,
- post,
- author of the post.';


--
-- Name: person person_id_key; Type: CONSTRAINT; Schema: actor; Owner: halftest
--

ALTER TABLE ONLY actor.person
    ADD CONSTRAINT person_id_key UNIQUE (id);


--
-- Name: person person_pkey; Type: CONSTRAINT; Schema: actor; Owner: halftest
--

ALTER TABLE ONLY actor.person
    ADD CONSTRAINT person_pkey PRIMARY KEY (first_name, last_name, birth_date);


--
-- Name: comment comment_pkey; Type: CONSTRAINT; Schema: blog; Owner: halftest
--

ALTER TABLE ONLY blog.comment
    ADD CONSTRAINT comment_pkey PRIMARY KEY (id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: blog; Owner: halftest
--

ALTER TABLE ONLY blog.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (id);


--
-- Name: post post_pkey; Type: CONSTRAINT; Schema: blog; Owner: halftest
--

ALTER TABLE ONLY blog.post
    ADD CONSTRAINT post_pkey PRIMARY KEY (id);


--
-- Name: post author; Type: FK CONSTRAINT; Schema: blog; Owner: halftest
--

ALTER TABLE ONLY blog.post
    ADD CONSTRAINT author FOREIGN KEY (author_first_name, author_last_name, author_birth_date) REFERENCES actor.person(first_name, last_name, birth_date) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: comment author; Type: FK CONSTRAINT; Schema: blog; Owner: halftest
--

ALTER TABLE ONLY blog.comment
    ADD CONSTRAINT author FOREIGN KEY (author_id) REFERENCES actor.person(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: event author; Type: FK CONSTRAINT; Schema: blog; Owner: halftest
--

ALTER TABLE ONLY blog.event
    ADD CONSTRAINT author FOREIGN KEY (author_first_name, author_last_name, author_birth_date) REFERENCES actor.person(first_name, last_name, birth_date) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: comment post; Type: FK CONSTRAINT; Schema: blog; Owner: halftest
--

ALTER TABLE ONLY blog.comment
    ADD CONSTRAINT post FOREIGN KEY (post_id) REFERENCES blog.post(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: SCHEMA actor; Type: ACL; Schema: -; Owner: halftest
--

GRANT ALL ON SCHEMA actor TO halftest;


--
-- Name: SCHEMA blog; Type: ACL; Schema: -; Owner: halftest
--

GRANT ALL ON SCHEMA blog TO halftest;


--
-- Name: SCHEMA "blog.view"; Type: ACL; Schema: -; Owner: halftest
--

GRANT ALL ON SCHEMA "blog.view" TO halftest;


--
-- Name: SEQUENCE id_person; Type: ACL; Schema: actor; Owner: halftest
--

GRANT ALL ON SEQUENCE actor.id_person TO halftest;


--
-- Name: TABLE person; Type: ACL; Schema: actor; Owner: halftest
--

GRANT ALL ON TABLE actor.person TO halftest;


--
-- Name: SEQUENCE id_comment; Type: ACL; Schema: blog; Owner: halftest
--

GRANT ALL ON SEQUENCE blog.id_comment TO halftest;


--
-- Name: TABLE comment; Type: ACL; Schema: blog; Owner: halftest
--

GRANT ALL ON TABLE blog.comment TO halftest;


--
-- Name: SEQUENCE post_id; Type: ACL; Schema: blog; Owner: halftest
--

GRANT ALL ON SEQUENCE blog.post_id TO halftest;


--
-- Name: TABLE post; Type: ACL; Schema: blog; Owner: halftest
--

GRANT ALL ON TABLE blog.post TO halftest;


--
-- Name: TABLE event; Type: ACL; Schema: blog; Owner: halftest
--

GRANT ALL ON TABLE blog.event TO halftest;


--
-- Name: TABLE post_comment; Type: ACL; Schema: blog.view; Owner: halftest
--

GRANT ALL ON TABLE "blog.view".post_comment TO halftest;


--
-- PostgreSQL database dump complete
--
