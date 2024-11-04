from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
import psycopg2
import json
from datetime import timedelta
import os
import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
import psycopg2
import json
from datetime import timedelta

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'  # Используем простое кэширование в памяти
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Устанавливаем тайм-аут кэша на 5 минут
cache = Cache(app)

# Подключение к базе данных
with open('connections.json') as f:
    connections = json.load(f)
    db_config = connections['moovie_chooser']['postgres']
    secret = connections['secret_key']
    VIDEO_DIR = connections['video_dir']

app.secret_key = secret
app.permanent_session_lifetime = timedelta(minutes=30)  # Установка таймаута на 30 минут

conn = psycopg2.connect(
    host=db_config['host'],
    port=db_config['port'],
    dbname=db_config['db'],
    user=db_config['user'],
    password=db_config['password']
)

@app.route('/')
def index():
    """Страница авторизации."""
    return render_template('index.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    """Обработка логина пользователя."""
    message = None
    message_type = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            cur = conn.cursor()
            cur.execute('SELECT "login", "password", "is_active" FROM app.users WHERE login = %s AND is_active = True', (username,))
            user = cur.fetchone()
            
            if user:
                stored_hash = user[1]  # Предполагается, что хеш пароля находится на 2-й позиции
                is_active = user[2]     # Предполагается, что поле `is_active` находится на 3-й позиции

                # Проверка хеша пароля
                if check_password_hash(stored_hash, password):
                    if is_active:
                        session['user_id'] = user[0]
                        session.permanent = True
                        message = 'Успешный вход'
                        message_type = 'success'
                        return redirect(url_for('room'))
                    else:
                        message = 'Пользователь не подтвержден'
                        message_type = 'warning'
                else:
                    message = 'Неверные имя пользователя или пароль'
                    message_type = 'danger'
            else:
                message = 'Неверные имя пользователя или пароль'
                message_type = 'danger'
        
        except Exception as e:
            print(f"Ошибка при аутентификации: {e}")
            message = 'Ошибка при аутентификации'
            message_type = 'danger'
        finally:
            cur.close()
    
    return render_template('index.html', message=message, message_type=message_type)

@app.route('/register', methods=['GET', 'POST'])
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
        "birth_date": ""
    }

    if request.method == 'POST':
        # Заполняем form_data из формы
        form_data['username'] = request.form['username']
        form_data['first_name'] = request.form.get('first_name', "")
        form_data['surname'] = request.form.get('surname', "")
        form_data['email'] = request.form.get('email', "")
        form_data['phone'] = request.form.get('phone', "")
        form_data['birth_date'] = request.form.get('birth_date', "")

        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            message = 'Пароли не совпадают. Пожалуйста, попробуйте снова.'
            message_type = 'warning'
        else:
            try:
                # Проверка на существование пользователя
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM app.users WHERE login = %s", (form_data['username'],))
                    existing_user = cur.fetchone()

                    if existing_user:
                        message = 'Пользователь с таким именем уже существует'
                        message_type = 'warning'
                    else:
                        # Хэшируем пароль перед добавлением
                        hashed_password = generate_password_hash(password)
                        
                        # Вставка нового пользователя
                        cur.execute(
                            "INSERT INTO app.users (login, password, name, surname, email, phone, birth_date) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (form_data['username'], hashed_password, form_data['first_name'],
                             form_data['surname'], form_data['email'], form_data['phone'], form_data['birth_date'])
                        )
                        conn.commit()
                        message = 'Регистрация успешна!'
                        message_type = 'success'
                        return redirect(url_for('index'))

            except Exception as e:
                conn.rollback()
                print(f'Ошибка регистрации: {str(e)}')
                message = 'Ошибка регистрации. Пожалуйста, попробуйте снова.'
                message_type = 'danger'

    return render_template('register.html', message=message, message_type=message_type, form_data=form_data)

@cache.cached(timeout=300, key_prefix='movies_data')  # Кэшируем данные на 5 минут
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

@app.route('/room')
def room():
    """Главная страница после авторизации."""
    if 'user_id' in session:
        return render_template('room.html')
    return render_template('index.html', message='Пожалуйста, войдите в систему', message_type='warning')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    """Страница с таблицей фильмов."""
    message = None
    message_type = None

    if request.method == 'POST':
        name = request.form.get('name')
        word = request.form.get('word')
        
        if name and word:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO app.movies (offer, movie) VALUES (%s, %s)", (name, word))
                conn.commit()
                cache.delete('movies_data')
                message = 'Запись добавлена!'
                message_type = 'success'
                return redirect(url_for('submit'))
            
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                message = 'Такая запись уже существует'
                message_type = 'warning'
            except Exception as e:
                conn.rollback()
                print(f"Ошибка при добавлении записи: {e}")
                message = 'Ошибка при добавлении записи'
                message_type = 'danger'
            finally:
                cur.close()
    
    movies = get_movies()
    return render_template('submit.html', rows=movies, message=message, message_type=message_type)

@app.route('/logout', methods=['POST'])
def logout():
    """Выход из системы."""
    session.pop('user_id', None)
    return render_template('index.html', message='Вы вышли из системы', message_type='info')

@app.route('/get_random', methods=['POST'])
def get_random_entry():
    """Получение случайной записи из таблицы app.movies."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT offer, movie FROM app.movies ORDER BY RANDOM() LIMIT 1")
        chosen_entry = cur.fetchone()
    except Exception as e:
        print(f"Ошибка при получении случайной записи: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500
    finally:
        cur.close()

    if chosen_entry:
        return jsonify({'name': chosen_entry[0], 'word': chosen_entry[1]})
    else:
        return jsonify({'error': 'Нет данных'}), 404

@app.route('/delete_entry', methods=['POST'])
def delete_entry():
    """Удаление записи из таблицы app.movies по имени и описанию."""
    entry_to_delete = request.json
    if entry_to_delete:
        name = entry_to_delete.get('name')
        word = entry_to_delete.get('word')
        
        if name and word:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM app.movies WHERE offer = %s AND movie = %s", (name, word))
                conn.commit()
                cache.delete('movies_data')  # Удаляем кэш при удалении записи
                if cur.rowcount > 0:
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'message': 'Запись не найдена'}), 404

            except Exception as e:
                conn.rollback()
                print(f"Ошибка при удалении записи: {e}")
                return jsonify({'success': False, 'message': str(e)}), 400
            finally:
                cur.close()
    return jsonify({'success': False, 'message': 'Не удалось получить данные для удаления'}), 400

def get_random_video():
    """Получение случайного видео из указанной директории."""
    video_files = []
    for root, dirs, files in os.walk(VIDEO_DIR):
        for file in files:
            if file.endswith(('.mp4', '.mkv', '.avi')):
                video_files.append(os.path.join(root, file))
    return random.choice(video_files) if video_files else None

@app.route('/watch')
def watch():
    """Страница с видео-плеером."""
    video_path = get_random_video()
    if video_path:
        return render_template('watch.html', video_path=video_path)
    else:
        return "Нет доступных видео для просмотра.", 404

@app.route('/get_next_video')
def get_next_video():
    """Получение следующего видео."""
    video_path = get_random_video()
    if video_path:
        return jsonify({'video_path': video_path})
    else:
        return jsonify({'video_path': None})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)