-- create db
CREATE DATABASE movies;

-- create schema
DROP SCHEMA IF EXISTS app;
CREATE SCHEMA app;

-- users
DROP TABLE IF EXISTS app.users;

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
DROP TABLE IF EXISTS app.rooms;

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

-- movies

-- movie_rooms
DROP TABLE IF EXISTS app.movie_rooms;

CREATE TABLE app.movie_rooms (
	id serial4 NOT NULL,
	added_by int4 NOT NULL,
	room_id int4 NOT NULL,
	movie_id int4 NOT NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT movie_rooms_pkey PRIMARY KEY (id)
);
ALTER TABLE app.movie_rooms ADD CONSTRAINT movie_rooms_added_by_fkey FOREIGN KEY (added_by) REFERENCES app.users(id);
ALTER TABLE app.movie_rooms ADD CONSTRAINT movie_rooms_movie_id_fkey FOREIGN KEY (movie_id) REFERENCES app.movies(id);
ALTER TABLE app.movie_rooms ADD CONSTRAINT movie_rooms_room_id_fkey FOREIGN KEY (room_id) REFERENCES app.rooms(id);

-- movie_rooms_history
DROP TABLE IF EXISTS app.movie_rooms_history;

CREATE TABLE app.movie_rooms_history (
    id serial4 NOT NULL,
    added_by int4 NOT NULL,
    room_id int4 NOT NULL,
    movie_id int4 NOT NULL,
    created_at timestamp DEFAULT now() NOT NULL,
    rating int CHECK (rating >= 1 AND rating <= 10), -- Оценка от 1 до 10
    rated_by int4, -- Ссылка на пользователя, который оценил
    deleted_at timestamp DEFAULT now() NOT NULL, -- Дата и время удаления
    CONSTRAINT movie_rooms_history_pkey PRIMARY KEY (id),
    CONSTRAINT movie_rooms_history_added_by_fkey FOREIGN KEY (added_by) REFERENCES app.users(id),
    CONSTRAINT movie_rooms_history_movie_id_fkey FOREIGN KEY (movie_id) REFERENCES app.movies(id),
    CONSTRAINT movie_rooms_history_room_id_fkey FOREIGN KEY (room_id) REFERENCES app.rooms(id),
    CONSTRAINT movie_rooms_history_rated_by_fkey FOREIGN KEY (rated_by) REFERENCES app.users(id) -- Внешний ключ для rated_by
);

CREATE OR REPLACE FUNCTION log_movie_room_deletion_history() 
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO app.movie_rooms_history (added_by, room_id, movie_id, created_at)
    VALUES (OLD.added_by, OLD.room_id, OLD.movie_id, OLD.created_at); 
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_movie_room_delete_history
BEFORE DELETE ON app.movie_rooms
FOR EACH ROW EXECUTE FUNCTION log_movie_room_deletion_history();