create extension if not exists pgcrypto;

create table if not exists half_orm_meta.database (
    id text primary key,
    name text not null,
    description text
);


create or replace function half_orm_meta.check_database(old_dbid text default null) returns text as $$
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
$$ language plpgsql;

insert into half_orm_meta.database (id, name) values ((select half_orm_meta.check_database()), (select current_database()));

comment on table half_orm_meta.database is 'id identifies the database in the cluster. It uses the key in hop_key.';
