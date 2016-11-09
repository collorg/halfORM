# Installation (tested on Linux/Mac OSX)
- Install psycopg2 (see http://initd.org/psycopg/docs/install.html)
- clone ```halfORM``` and install it:
```sh
$ git clone https://github.com/collorg/halfORM
$ sudo pip3 install halfORM/
```

You're now ready to go!

## Upgrade halfORM to the last development release
In the ```halfORM``` directory run:
```sh
$ git pull
$ sudo pip3 install --upgrade .
```

## Uninstall halfORM
run ```sudo pip3 uninstall half-orm```

# Installation of the halftest database
You must have PostgreSQL superuser acces. In the ```halfORM``` directory, run:

```sh
$ psql template1 -f test/sql/halftest.sql
```
It creates a ```halftest``` user with the password ```halftest```  and the  ```halftest``` database.

## Uninstallation of the halftest database
```sh
$ dropdb halftest
$ dropuser halftest
```
