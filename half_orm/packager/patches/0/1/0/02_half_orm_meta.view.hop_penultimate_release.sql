drop view if exists "half_orm_meta.view".hop_penultimate_release;
create view "half_orm_meta.view".hop_penultimate_release as
select * from (select major, minor, patch from half_orm_meta.hop_release order by major desc, minor desc, patch desc limit 2 ) as penultimate order by major, minor, patch limit 1;
