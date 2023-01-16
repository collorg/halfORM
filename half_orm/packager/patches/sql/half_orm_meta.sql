--
-- PostgreSQL database dump
--

-- Dumped from database version 15.1 (Debian 15.1-1.pgdg110+1)
-- Dumped by pg_dump version 15.1 (Debian 15.1-1.pgdg110+1)

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
-- Name: half_orm_meta; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA half_orm_meta;


--
-- Name: half_orm_meta.view; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA "half_orm_meta.view";


SET default_tablespace = '';

SET default_table_access_method = heap;

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
-- Name: hop_release_issue hop_release_issue_release_major_release_minor_release_patc_fkey; Type: FK CONSTRAINT; Schema: half_orm_meta; Owner: -
--

ALTER TABLE ONLY half_orm_meta.hop_release_issue
    ADD CONSTRAINT hop_release_issue_release_major_release_minor_release_patc_fkey FOREIGN KEY (release_major, release_minor, release_patch, release_pre_release, release_pre_release_num) REFERENCES half_orm_meta.hop_release(major, minor, patch, pre_release, pre_release_num);


--
-- PostgreSQL database dump complete
--

