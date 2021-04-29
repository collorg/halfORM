create view "meta.view".last_release as
select * from meta.release order by major desc, minor desc, patch desc limit 1;
