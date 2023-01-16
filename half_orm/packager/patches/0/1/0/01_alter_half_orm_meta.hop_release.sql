alter table half_orm_meta.hop_release add column dbid text references half_orm_meta.database(id) on update cascade;
alter table half_orm_meta.hop_release add column hop_release text;
