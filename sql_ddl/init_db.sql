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
	"name" varchar,
	surname varchar,
	phone varchar,
	email varchar,
	birth_date date,
	"password" varchar NOT NULL,
	communication_consent bool DEFAULT false NOT NULL,
	personal_data_consent bool DEFAULT false NOT NULL;
	is_active bool DEFAULT false NOT NULL,
    created_at timestamp NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now()
);

COMMENT ON COLUMN app.users.id IS 'Уникальный ID пользователя';
COMMENT ON COLUMN app.users.login IS 'Уникальный в ситсеме логин';
COMMENT ON COLUMN app.users."name" IS 'Имя';
COMMENT ON COLUMN app.users.surname IS 'Фамилия';
COMMENT ON COLUMN app.users.phone IS 'Номер телефона';
COMMENT ON COLUMN app.users.email IS 'Электронная почта';
COMMENT ON COLUMN app.users."password" IS 'Пароль';
COMMENT ON COLUMN app.users.is_active IS 'Признак активности пользователя';
COMMENT ON COLUMN app.users.created_at IS 'Дата создания аккаунта';
COMMENT ON COLUMN app.users.updated_at IS 'Дата и время обновления аккаунта';
COMMENT ON COLUMN app.users.birth_date IS 'Дата рожждения';
COMMENT ON COLUMN app.users.communication_consent IS 'Согласие на коммуникацию по смс и емейлам';
COMMENT ON COLUMN app.users.personal_data_consent IS 'Согласие на обработку и персональных данных и её передачу третьим лицам';

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
