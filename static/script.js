document.addEventListener('DOMContentLoaded', function() {
    // Сообщение о загрузке страницы и инициализации кода
    console.log("Страница загружена, скрипт инициализирован.");

    // Инициализация кнопки выбора случайной записи
    const goButton = document.getElementById('goButton');
    if (goButton) {
        goButton.addEventListener('click', async function() {
            try {
                const response = await fetch('/get_random', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
    
                const result = await response.json();
                const resultDiv = document.getElementById('result');
    
                if (response.ok) {
                    goButton.style.display = 'none';
                    resultDiv.innerHTML = `
                        <div>Победитель ${result.name}</div> 
                        <div>Фильм ${result.word}</div>
                        <div>
                            <button id="deleteButton">Удалить фильм</button>
                            <button id="replayButton">Переиграть</button>
                        </div>
                    `;
    
                    document.getElementById('deleteButton').addEventListener('click', async function() {
                        await fetch('/delete_entry', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(result),
                        });
                        resultDiv.innerText = 'Фильм удален.';
                        goButton.style.display = 'inline-block';
                    });
    
                    document.getElementById('replayButton').addEventListener('click', function() {
                        goButton.click();
                    });
    
                } else {
                    goButton.style.display = 'none';
                    resultDiv.innerText = 'Не добавлено ни одной записи, хотите добавить?';
                }
            } catch (error) {
                console.error('Ошибка:', error);
            }
        });
    }

    // Лог для кнопок удаления записи на странице submit.html
    const deleteButtons = document.querySelectorAll('.delete-btn');
    console.log(`Обнаружено ${deleteButtons.length} кнопок удаления.`);

    deleteButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const name = this.getAttribute('data-name');
            const word = this.getAttribute('data-word');
            console.log(`Удаление записи: ${name}, ${word}`);

            try {
                const response = await fetch('/delete_entry', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name: name, word: word }),
                });

                if (response.ok) {
                    // Удаляем строку из таблицы на клиенте
                    this.closest('tr').remove();
                    console.log('Запись успешно удалена.');
                    alert('Запись удалена.');
                } else {
                    console.error('Ошибка при удалении записи.');
                    alert('Ошибка при удалении записи.');
                }
            } catch (error) {
                console.error('Ошибка запроса:', error);
            }
        });
    });
});
