from flask import Flask, render_template, request, jsonify
import csv
import random
import os

app = Flask(__name__)

# Путь к CSV файлу
DATA_FILE = 'data/data.csv'

# Функция для проверки и создания файла, если он не существует
def ensure_data_file_exists():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8'):
            pass

# Главная страница
@app.route('/')
def home():
    return render_template('index.html')

# Страница добавления записи и просмотр базы
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    ensure_data_file_exists()
    message = None
    if request.method == 'POST':
        name = request.form.get('name')
        word = request.form.get('word')
        if name and word:
            with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([name, word])
            message = 'Запись добавлена!'
    with open(DATA_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
    return render_template('submit.html', rows=rows, message=message)

# Получение и удаление случайной строки
@app.route('/get_random', methods=['POST'])
def get_random_entry():
    ensure_data_file_exists()
    with open(DATA_FILE, mode='r', encoding='utf-8') as file:
        reader = list(csv.reader(file))

    if reader:
        chosen_entry = random.choice(reader)
        return jsonify({'name': chosen_entry[0], 'word': chosen_entry[1]})
    else:
        return jsonify({'error': 'Нет данных'}), 404

# Удаление записи
@app.route('/delete_entry', methods=['POST'])
def delete_entry():
    entry_to_delete = request.json
    if entry_to_delete:
        try:
            # Читаем текущие записи
            with open(DATA_FILE, mode='r', encoding='utf-8') as file:
                rows = list(csv.reader(file))

            # Удаляем запись, которую нужно удалить
            updated_entries = [entry for entry in rows if entry != [entry_to_delete['name'], entry_to_delete['word']]]

            # Записываем обновленный список обратно в CSV-файл
            with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(updated_entries)

            return jsonify({'success': True})
        except Exception as e:
            print(f"Ошибка при удалении записи: {e}")
            return jsonify({'success': False, 'message': str(e)}), 400
    return jsonify({'success': False, 'message': 'Не удалось получить данные для удаления'}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
