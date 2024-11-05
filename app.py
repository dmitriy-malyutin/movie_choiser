import json
import os
import random
import re
from datetime import timedelta
from pymongo import MongoClient
import psycopg2
from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_caching import Cache
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["CACHE_TYPE"] = "simple"  # Используем простое кэширование в памяти
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # Устанавливаем тайм-аут кэша на 5 минут
cache = Cache(app)

# Подключение к базе данных
with open("connections.json") as f:
    connections = json.load(f)
    db_config = connections["dbs"]["postgres"]
    mongo_uri = connections["dbs"]["mongo_uri"]
    secret = connections["secret_key"]
    VIDEO_DIR = connections["video_dir"]

client = MongoClient(mongo_uri)
db = client["movie_choiser"]  # Имя вашей базы данных
movies_collection = db['movies'] 

app.secret_key = secret
app.permanent_session_lifetime = timedelta(minutes=30)  # Установка таймаута на 30 минут

conn = psycopg2.connect(
    host=db_config["host"],
    port=db_config["port"],
    dbname=db_config["db"],
    user=db_config["user"],
    password=db_config["password"],
)




@app.route("/")
def index():
    """Страница авторизации."""
    return render_template("index.html")


@app.route("/auth", methods=["GET", "POST"])
def auth():
    """Обработка логина пользователя."""
    message = None
    message_type = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT "login", "password", "is_active" FROM app.users WHERE login = %s AND is_active = True',
                (username,),
            )
            user = cur.fetchone()

            if user:
                stored_hash = user[
                    1
                ]  # Предполагается, что хеш пароля находится на 2-й позиции
                is_active = user[
                    2
                ]  # Предполагается, что поле `is_active` находится на 3-й позиции

                # Проверка хеша пароля
                if check_password_hash(stored_hash, password):
                    if is_active:
                        session["user_id"] = user[0]
                        session.permanent = True
                        message = "Успешный вход"
                        message_type = "success"
                        return redirect(url_for("home"))
                    else:
                        message = "Пользователь не подтвержден"
                        message_type = "warning"
                else:
                    message = "Неверные имя пользователя или пароль"
                    message_type = "danger"
            else:
                message = "Неверные имя пользователя или пароль"
                message_type = "danger"

        except Exception as e:
            print(f"Ошибка при аутентификации: {e}")
            message = "Ошибка при аутентификации"
            message_type = "danger"
        finally:
            cur.close()

    return render_template("index.html", message=message, message_type=message_type)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Обработка регистрации нового пользователя."""
    message = None  # Сообщение об ошибке или успехе
    message_type = None  # Тип сообщения ('success' или 'warning')

    # Сохраняем введённые данные для отображения их при ошибке
    form_data = {
        "username": "",
        "first_name": "",
        "surname": "",
        "email": "",
        "phone": "",
        "birth_date": "",
    }

    if request.method == "POST":
        # Заполняем form_data из формы
        form_data["username"] = request.form["username"]
        form_data["first_name"] = request.form.get("first_name", "")
        form_data["surname"] = request.form.get("surname", "")
        form_data["email"] = request.form.get("email", "")
        form_data["phone"] = request.form.get("phone", "")
        form_data["birth_date"] = request.form.get("birth_date", "")

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            message = "Пароли не совпадают. Пожалуйста, попробуйте снова."
            message_type = "warning"
        else:
            try:
                # Проверка на существование пользователя
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM app.users WHERE login = %s",
                        (form_data["username"],),
                    )
                    existing_user = cur.fetchone()

                    if existing_user:
                        message = "Пользователь с таким именем уже существует"
                        message_type = "warning"
                    else:
                        # Хэшируем пароль перед добавлением
                        hashed_password = generate_password_hash(password)

                        # Вставка нового пользователя
                        cur.execute(
                            "INSERT INTO app.users (login, password, name, surname, email, phone, birth_date) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (
                                form_data["username"],
                                hashed_password,
                                form_data["first_name"],
                                form_data["surname"],
                                form_data["email"],
                                form_data["phone"],
                                form_data["birth_date"],
                            ),
                        )
                        conn.commit()
                        message = "Регистрация успешна!"
                        message_type = "success"
                        return redirect(url_for("index"))

            except Exception as e:
                conn.rollback()
                print(f"Ошибка регистрации: {str(e)}")
                message = "Ошибка регистрации. Пожалуйста, попробуйте снова."
                message_type = "danger"

    return render_template(
        "register.html", message=message, message_type=message_type, form_data=form_data
    )


@cache.cached(timeout=300, key_prefix="movies_data")  # Кэшируем данные на 5 минут
def get_movies():
    """Получение данных о фильмах из таблицы app.movies."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT offer, movie FROM app.movies")
        movies = cur.fetchall()
    except Exception as e:
        print(f"Ошибка при получении данных о фильмах: {e}")
        movies = []
    finally:
        cur.close()
    return movies


@app.route("/home")
def home():
    """Главная страница после авторизации."""
    if "user_id" in session:
        return render_template("home.html")
    return render_template(
        "index.html", message="Пожалуйста, войдите в систему", message_type="warning"
    )


@app.route("/submit", methods=["GET", "POST"])
def submit():
    """Страница с таблицей фильмов."""
    message = None
    message_type = None

    if request.method == "POST":
        name = request.form.get("name")
        word = request.form.get("word")

        if name and word:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO app.movies (offer, movie) VALUES (%s, %s)",
                    (name, word),
                )
                conn.commit()
                cache.delete("movies_data")
                message = "Запись добавлена!"
                message_type = "success"
                return redirect(url_for("submit"))

            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                message = "Такая запись уже существует"
                message_type = "warning"
            except Exception as e:
                conn.rollback()
                print(f"Ошибка при добавлении записи: {e}")
                message = "Ошибка при добавлении записи"
                message_type = "danger"
            finally:
                cur.close()

    movies = get_movies()
    return render_template(
        "submit.html", rows=movies, message=message, message_type=message_type
    )


@app.route("/logout", methods=["POST"])
def logout():
    """Выход из системы."""
    session.pop("user_id", None)
    return render_template(
        "index.html", message="Вы вышли из системы", message_type="info"
    )


@app.route("/get_random_entry", methods=["GET"])
def get_random_entry():
    """Получение случайной записи из таблицы app.movies."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT offer, movie FROM app.movies ORDER BY RANDOM() LIMIT 1")
        chosen_entry = cur.fetchone()
    except Exception as e:
        print(f"Ошибка при получении случайной записи: {e}")
        return jsonify({"error": "Ошибка сервера"}), 500
    finally:
        cur.close()

    if chosen_entry:
        return jsonify({"name": chosen_entry[0], "word": chosen_entry[1]})
    else:
        return jsonify({"error": "Нет данных"}), 404


@app.route("/delete_entry", methods=["POST"])
def delete_entry():
    """Удаление записи из таблицы app.movies по имени и описанию."""
    entry_to_delete = request.json
    if entry_to_delete:
        name = entry_to_delete.get("name")
        word = entry_to_delete.get("word")

        if name and word:
            try:
                cur = conn.cursor()
                cur.execute(
                    "DELETE FROM app.movies WHERE offer = %s AND movie = %s",
                    (name, word),
                )
                conn.commit()
                cache.delete("movies_data")  # Удаляем кэш при удалении записи
                if cur.rowcount > 0:
                    return jsonify({"success": True})
                else:
                    return (
                        jsonify({"success": False, "message": "Запись не найдена"}),
                        404,
                    )

            except Exception as e:
                conn.rollback()
                print(f"Ошибка при удалении записи: {e}")
                return jsonify({"success": False, "message": str(e)}), 400
            finally:
                cur.close()
    return (
        jsonify(
            {"success": False, "message": "Не удалось получить данные для удаления"}
        ),
        400,
    )


# Воспроизведение случайной серии
def find_video_file(video_name):
    """Поиск файла по имени в VIDEO_DIR и возврат полного имени без расширения."""
    for root, dirs, files in os.walk(VIDEO_DIR):
        for file in files:
            # Проверяем, содержит ли файл имя `video_name` и подходит ли по шаблону.
            if video_name in file:
                # Возвращаем полный путь и имя файла без расширения.
                full_name = os.path.splitext(file)[0]
                return os.path.join(root, file), full_name
    return None, None


def get_next_episode(current_video_name, series_name_pattern=None):
    """
    Получение следующей серии на основе текущего имени видео.
    series_name_pattern - шаблон регулярного выражения для поиска названия сериала.
    """
    if not series_name_pattern:
        series_name_pattern = r"(.*?)\s(\d+)x(\d+)"

    match = re.match(series_name_pattern, current_video_name)
    if match:
        series_name = match.group(1).strip()
        season = int(match.group(2))
        episode = int(match.group(3))

        next_episode = episode + 1
        next_video_name = f"{series_name} {season}x{next_episode:02d}"

        next_video_path, full_name = find_video_file(next_video_name)
        if next_video_path:
            return {
                "path": next_video_path,
                "name": full_name,  # Полное имя файла без расширения
                "extension": next_video_path.split(".")[-1],
            }

        next_episode = 1
        next_season = season + 1
        next_video_name = f"{series_name} {next_season}x{next_episode:02d}"
        next_video_path, full_name = find_video_file(next_video_name)

        if next_video_path:
            return {
                "path": next_video_path,
                "name": full_name,
                "extension": next_video_path.split(".")[-1],
            }

    return None


def get_random_video():
    """Получение случайного видео, с учетом равной вероятности для каждого сериала."""

    # Получаем список всех папок на уровень ниже внутри `VIDEO_DIR`
    series_dirs = [os.path.join(VIDEO_DIR, d) for d in os.listdir(VIDEO_DIR) if os.path.isdir(os.path.join(VIDEO_DIR, d))]

    # Если нет папок с сериалами, возвращаем None
    if not series_dirs:
        return None

    selected_series_dir = random.choice(series_dirs)
       # Собираем список всех видеофайлов в выбранной папке
    video_files = []
    for root, dirs, files in os.walk(selected_series_dir):
        for file in files:
            if file.endswith((".mp4")):
                video_files.append(os.path.join(root, file))
        # Если нет видеофайлов, возвращаем None
    if not video_files:
        return None

    # Выбираем случайный видеофайл
    selected_video = random.choice(video_files)
    relative_path = os.path.relpath(selected_video, VIDEO_DIR)
    web_path = f"static/series/{relative_path}"
    video_name = os.path.basename(selected_video).rsplit(".", 1)[0]
    video_extension = os.path.basename(selected_video).split(".")[-1]

    return {
        "path": web_path,
        "video_name": video_name,
        "extension": video_extension,
    }


@app.route("/watch_random")
def watch_random():
    """Страница с видео-плеером для случайной серии."""
    video = get_random_video()
    if video:
        return render_template("watch_random.html", video=video)
    else:
        return "Нет доступных видео для просмотра.", 404


@app.route("/get_next_video")
def get_next_video():
    """Маршрут для получения следующего видео."""
    current_video_name = request.args.get("current_video_name")
    next_video = get_next_episode(current_video_name)
    if next_video:
        return jsonify(
            {
                "video_path": next_video["path"],
                "video_name": next_video["name"],
                "video_extension": next_video["extension"],
            }
        )
    else:
        return jsonify(
            {"video_path": None, "video_name": None, "video_extension": None}
        )


@app.route("/get_random")
def get_random():
    """Маршрут для получения случайного видео."""
    random_video = get_random_video()
    if random_video:
        return jsonify(
            {
                "video_path": random_video["path"],
                "video_name": random_video["video_name"],
                "video_extension": random_video["extension"],
            }
        )
    else:
        return jsonify(
            {"video_path": None, "video_name": None, "video_extension": None}
        )


@app.route("/room", methods=["GET"])
def room():
    return render_template("room.html")

# MONGO MOVIES
@app.route('/movies')
def all_movies():
    page = int(request.args.get('page', 1))  # Текущая страница, по умолчанию 1
    per_page = 20                            # Количество фильмов на странице
    offset = (page - 1) * per_page            # Смещение для запроса

    # Запрос на фильмы с ограничением по смещению и количеству
    movies = list(movies_collection.find({}).skip(offset).limit(per_page))
    total_movies = movies_collection.count_documents({})  # Общее количество фильмов
    total_pages = (total_movies + per_page - 1) // per_page

    return render_template(
        'all_movies.html',
        movies=movies,
        page=page,
        total_pages=total_pages
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
