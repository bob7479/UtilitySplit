
drop table if exists entries;
drop table if exists users;
drop table if exists bills;
drop table if exists users_bills;


-- drop table if exists bills;
drop table if exists users_bills;
create table entries (
	id integer primary key autoincrement,
	title text not null,
	'text' text not null
);

create table users (
	id integer primary key autoincrement,
	username text not null,
	password text not null
);

create table bills (
	id integer primary key autoincrement,
	username text not null,
	billname text not null, 
	category text not null,
	frequency integer not null, 
	cost decimal not null
);

create table users_bills (
	id integer primary key autoincrement,
	username text not null,
	billname text not null, 
	paid boolean not null
);

-- select username, billname, paid from users 
-- join users_bills on users_bills.username = users.username 
-- join bills on bills.billname = users_bills.billname;