create view "meta.view".last_release as
select * from meta.release order by major desc, minor desc, patch, pre_release, pre_release_num desc limit 1;
