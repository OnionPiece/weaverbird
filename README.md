# weaverbird

## Refer

https://medium.com/@saikrishna.d/get-create-database-models-for-existing-database-tables-with-nodejs-python-51dc0856abd7
https://stackoverflow.com/questions/11046039/sqlalchemy-import-tables-with-relationships

## Target

The target of this project is try to build a tool to generate sandbox to try
and test db migration via alembic.

For basic alembic usage, check https://alembic.sqlalchemy.org/en/latest/tutorial.html

搭建一个具有目标数据库的数据结构和数据的沙盒，然后利用此沙盒进行db migration
(使用alembic)的测试。

It supposes that:

  - developers and operators are not familiar with DB migration(alembic);
  - operators are not familiar with existiong DB tables schema;
  - team has a pre-announce environment, which has data to keep to do
    compatibility test and long-term tracking, which means it's not a
    suitable place to try and test DB migration scripts;
  - and for envrionment to try and test DB migration scripts, data from
    pre-announce env is need to do compatiblity test for new features.

### sqlacodegen

Should try it.

## What it will do

It will:

  - setup a mysql container with docker;
  - expose an existing DB tables to ORM files in python;
  - generate an init alembic script for existing DB tables schema;
  - transit data from existing DB to mysql container;

then user can to generate new DB migration script with alembic.

## Up to now

  - run_docker_mysql.sh can setup a mysql:5.5 container(sandbox), only for
    mysql 5.5 currently;
  - conf.json.temp, as a template for user to configure their DB information, and rows_slice_len(if data are too many, rows will be sliced, and commit to target DB table in turn). User need create a file named conf.json.
  - prepare.py will clean origin alembic files, export existing database tables
    to sqlalchemy models, and create the same tables in sandbox mysql;
  - data_migrate.py will try to migrate data from existing database to sandbox.

  - 运行run_docker_mysql.sh可以跑起一个mysql 5.5的容器(沙盒)
  - copy conf.json.temp到conf.json，讲数据库等配置信息写入到conf.json中
  - 运行prepare.py将会清理已经存在alembic相关的文件，然后从解析并到处目标数据
    表的ORM到models目录下，然后在沙盒中创建出同样的表
  - 运行data_migrate.py会尝试从目标数据中将数据导入到沙盒数据库

### I've test...

Target DB is running in contrainer, and:
 - source DB is running on a remote server;
 - source DB is running  in a container.

### Limits to prepare.py and data_migrate.py

Only for mysql 5.5.

Type verified:
  - int, with display_width, with default
  - bigint, with display_width, with default
  - tinyint, with display_width, with default
  - varchar, with length, with default
  - decimal, with precision and scale
  - mediumtext
  - datatime, with default "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
  - timestamp
  - text
  - longtext

Other:
  - primary key
  - nullable
  - auto_increment
  - foreign_key
