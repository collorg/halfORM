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
-- Name: half_orm_meta; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA half_orm_meta;


--
-- Name: half_orm_meta.view; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA "half_orm_meta.view";


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


SET default_tablespace = '';

SET default_table_access_method = heap;

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

