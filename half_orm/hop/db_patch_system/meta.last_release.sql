create view "meta.view".last_release as
select * from meta.release order by major desc, minor desc, patch desc, pre_release desc, pre_release_num desc limit 1;
