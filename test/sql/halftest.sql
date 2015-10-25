create user halftest password 'halftest';
create database halftest owner halftest;

\c halftest halftest

create table personne( nom text, prenom text, date_naiss date, primary key(nom, prenom, date_naiss));

create table billet( texte text, nom text, prenom text, date_naiss date);

alter table billet add constraint "auteur" foreign key(nom, prenom, date_naiss) references personne;

