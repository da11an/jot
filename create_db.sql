PRAGMA foreign_keys = ON;

CREATE TABLE Notes (
	notes_id integer PRIMARY KEY AUTOINCREMENT,
	status_id integer,
	due integer,
	description text,
	created_at datetime NOT NULL DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')),
	modified_at datetime NOT NULL DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')),
	priority integer,
	alias text
);

CREATE TABLE Alias (
	notes_id integer,
	alias text,
	FOREIGN KEY (notes_id)
	       REFERENCES Notes (notes_id)
);

CREATE TRIGGER default_alias_from_id
AFTER INSERT ON Alias
FOR EACH ROW
WHEN NEW.alias IS NULL
BEGIN
    UPDATE Alias SET alias = cast(NEW.notes_id as text) WHERE rowid = NEW.rowid;
END;

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

INSERT INTO Status(status) values ('o=o'), ('[ ]'), ('[x]'), ('[0]'), ('[\]');
