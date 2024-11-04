-- create db
CREATE DATABASE movies;

-- create schema
CREATE SCHEMA app;

-- users
CREATE TABLE app.users (
	id serial4 NOT NULL,
	login varchar NOT NULL,
	"name" varchar,
	surname varchar,
	phone varchar,
	email varchar,
	"password" varchar NOT NULL,
	is_active bool DEFAULT false NOT NULL,
    created_at timestamp NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now()
);

