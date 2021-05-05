create table meta.release_issue (
    num int check (num >= 0),
    issue_release int default 0,
    release_major int not null,
    release_minor int not null,
    release_patch int not null,
    release_pre_release text not null,
    release_pre_release_num text not null,
    foreign key (
        release_major,
        release_minor,
        release_patch,
        release_pre_release,
        release_pre_release_num) references
    meta.release(
        major,
        minor,
        patch,
        pre_release,
        pre_release_num
    ),
    changelog text,
    primary key(num, issue_release)
);
