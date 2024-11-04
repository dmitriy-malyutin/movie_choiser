-- create db
CREATE DATABASE movies;

-- create schema
CREATE SCHEMA app;

-- users
CREATE TABLE app.users (
	id serial4 NOT NULL,
	login varchar NOT NULL,
	"name" varchar NULL,
	surname varchar NULL,
	phone varchar NULL,
	email varchar NULL,
	"password" varchar NOT NULL,
	is_active bool DEFAULT false NOT NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	birth_date date NULL,
	CONSTRAINT unique_id UNIQUE (id),
	CONSTRAINT unique_login UNIQUE (login)
);


-- rooms
CREATE TABLE app.rooms (
	id serial4 NOT NULL,
	room_name varchar NOT NULL,
	room_type varchar NOT NULL,
	member_ids _int4 NOT NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	created_by int4 NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	updated_by int4 NOT NULL,
	CONSTRAINT rooms_pkey PRIMARY KEY (id),
	CONSTRAINT uniq_room_name_created_by UNIQUE (room_name, created_by)
);
ALTER TABLE app.rooms ADD CONSTRAINT rooms_created_by_fkey FOREIGN KEY (created_by) REFERENCES app.users(id);
ALTER TABLE app.rooms ADD CONSTRAINT rooms_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES app.users(id);
