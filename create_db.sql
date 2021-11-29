CREATE TABLE Notes (
	notes_id integer PRIMARY KEY AUTOINCREMENT,
	status_id integer,
	due integer,
	description text,
	created_at datetime NOT NULL DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')),
	modified_at datetime NOT NULL DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime'))
);

CREATE TABLE Status (
	status_id integer PRIMARY KEY AUTOINCREMENT,
	status varchar
);

CREATE TABLE Nest (
	nest_id integer PRIMARY KEY AUTOINCREMENT,
	Parent integer,
	Child integer
);

CREATE TABLE Files (
	file_id integer PRIMARY KEY AUTOINCREMENT,
	file blob
);

CREATE TABLE NoteFiler (
	notefiler_id integer PRIMARY KEY AUTOINCREMENT,
	file_id integer,
	notes_id integer
);

--populate tables

INSERT INTO Status(status) values ('-->'), ('[ ]'), ('[x]'), ('[0]');
