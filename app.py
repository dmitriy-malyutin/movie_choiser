from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import json
import random
import csv
from datetime import timedelta
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Страница авторизации."""
    return render_template('index.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    """Обработка логина пользователя."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Проверка логина и пароля
        cur = conn.cursor()
        # Проверяем, существует ли пользователь с правильными данными и подтвержденный
        cur.execute("SELECT * FROM app.users WHERE name = %s AND password = %s AND is_active = True", (username, password))
        user = cur.fetchone()
        
        if user:
            if user[3]:  # Предполагается, что is_valid находится на 4-й позиции
                session['user_id'] = user[0]  # Сохраняем id пользователя в сессии
                session.permanent = True  # Сделать сессию постоянной
                flash('Успешный вход', 'success')
                return redirect(url_for('home'))  # Переход на главную страницу
            else:
                flash('Пользователь не подтвержден', 'warning')
                return redirect(url_for('index'))  # Возврат на страницу авторизации
        else:
            flash('Неверные имя пользователя или пароль', 'danger')
            return redirect(url_for('index'))  # Возврат на страницу авторизации в случае ошибки
    
    return redirect(url_for('index'))  # Возврат на страницу авторизации в случае ошибки

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Обработка регистрации нового пользователя."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Добавление нового пользователя в базу данных
        cur = conn.cursor()
        cur.execute("INSERT INTO app.users (name, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

def get_movies():
    """Получение данных о фильмах из таблицы app.movies."""
    cur = conn.cursor()
    cur.execute("SELECT offer, movie FROM app.movies")
    movies = cur.fetchall()
    cur.close()
    return movies

@app.route('/home')
def home():
    """Главная страница после авторизации."""
    if 'user_id' in session:  # Проверка, авторизован ли пользователь
        return render_template('home.html')
    flash('Пожалуйста, войдите в систему', 'warning')
    return redirect(url_for('index'))

# Страница добавления записи и просмотр базы
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    """Страница с таблицей фильмов."""
    message = None
    if request.method == 'POST':
        name = request.form.get('name')
        word = request.form.get('word')
        
        # Добавляем новую запись в таблицу фильмов
        if name and word:
            cur = conn.cursor()
            cur.execute("INSERT INTO app.movies (offer, movie) VALUES (%s, %s)", (name, word))
            conn.commit()
            cur.close()
            message = 'Запись добавлена!'
    
    # Получение данных о фильмах из базы данных
    movies = get_movies()
    return render_template('submit.html', rows=movies, message=message)

@app.route('/logout', methods=['POST'])
def logout():
    """Выход из системы."""
    session.pop('user_id', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

# Получение и удаление случайной строки
@app.route('/get_random', methods=['POST'])
def get_random_entry():
    """Получение случайной записи из таблицы app.movies."""
    try:
        cur = conn.cursor()
        # Выбор случайной записи
        cur.execute("SELECT offer, movie FROM app.movies ORDER BY RANDOM() LIMIT 1")
        chosen_entry = cur.fetchone()
        cur.close()

        if chosen_entry:
            return jsonify({'name': chosen_entry[0], 'word': chosen_entry[1]})
        else:
            return jsonify({'error': 'Нет данных'}), 404

    except Exception as e:
        print(f"Ошибка при получении случайной записи: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500


# Удаление записи
@app.route('/delete_entry', methods=['POST'])
def delete_entry():
    """Удаление записи из таблицы app.movies по имени и описанию."""
    entry_to_delete = request.json
    if entry_to_delete:
        name = entry_to_delete.get('name')
        word = entry_to_delete.get('word')
        
        if name and word:
            try:
                # Удаление записи из базы данных
                cur = conn.cursor()
                cur.execute("DELETE FROM app.movies WHERE offer = %s AND movie = %s", (name, word))
                conn.commit()
                cur.close()

                # Проверяем, было ли удалено что-то
                if cur.rowcount > 0:
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'message': 'Запись не найдена'}), 404

            except Exception as e:
                print(f"Ошибка при удалении записи: {e}")
                return jsonify({'success': False, 'message': str(e)}), 400
    return jsonify({'success': False, 'message': 'Не удалось получить данные для удаления'}), 400


if __name__ == '__main__':
    # Подключение к базе данных
    with open('connections.json') as f:
        connections = json.load(f)
        db_config = connections['moovie_chooser']['postgres']
        secret = connections['secret_key']

    app.secret_key = secret
    app.permanent_session_lifetime = timedelta(hours=1)  # Установка таймаута на 1 час
        
    conn = psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        dbname=db_config['db'],
        user=db_config['user'],
        password=db_config['password']
    )

    app.run(debug=True, host='0.0.0.0', port=5000)
