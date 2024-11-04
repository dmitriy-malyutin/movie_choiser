document.addEventListener('DOMContentLoaded', function() {
    console.log("Страница загружена, скрипт инициализирован.");

    // Настройка плеера и кнопки для следующего видео
    const videoPlayer = document.getElementById('videoPlayer');
    const nextButton = document.getElementById('nextButton');

    videoPlayer.addEventListener('ended', function() {
        fetch('/get_next_video')
            .then(response => response.json())
            .then(data => {
                if (data.video_path) {
                    videoPlayer.src = data.video_path;
                    videoPlayer.play();
                } else {
                    nextButton.style.display = 'block';
                }
            });
    });

    nextButton.addEventListener('click', function() {
        fetch('/get_next_video')
            .then(response => response.json())
            .then(data => {
                if (data.video_path) {
                    videoPlayer.src = data.video_path;
                    videoPlayer.play();
                    nextButton.style.display = 'none';
                }
            });
    });

    // Инициализация кнопки для случайного выбора записи
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
                        <div style="font-size: 24px;">Победитель: ${result.name}</div> 
                        <div style="font-size: 24px;">Фильм: ${result.word}</div>
                        <div>
                            <button id="deleteButton">Просмотрено, удалить</button>
                            <button id="replayButton">Переиграть</button>
                        </div>
                    `;

                    // Обработчик для кнопки удаления
                    document.getElementById('deleteButton').addEventListener('click', async function() {
                        try {
                            const deleteResponse = await fetch('/delete_entry', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify(result),
                            });

                            if (deleteResponse.ok) {
                                resultDiv.innerText = 'Фильм удален.';
                                goButton.style.display = 'inline-block';
                            } else {
                                const errorData = await deleteResponse.json();
                                console.error('Ошибка при удалении записи:', errorData.message);
                                alert('Ошибка при удалении записи.');
                            }
                        } catch (error) {
                            console.error('Ошибка запроса при удалении:', error);
                        }
                    });

                    // Обработчик для кнопки переиграть
                    document.getElementById('replayButton').addEventListener('click', function() {
                        goButton.click();
                    });
                } else {
                    goButton.style.display = 'none';
                    resultDiv.innerText = 'Не добавлено ни одной записи, хотите добавить?';
                }
            } catch (error) {
                console.error('Ошибка запроса:', error);
                document.getElementById('result').innerText = 'Произошла ошибка при получении данных.';
            }
        });
    }

    // Лог для кнопок удаления записи
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
                    this.closest('tr').remove();
                    console.log('Запись успешно удалена.');
                    alert('Запись удалена.');
                } else {
                    const errorData = await response.json();
                    console.error('Ошибка при удалении записи:', errorData.message);
                    alert('Ошибка при удалении записи.');
                }
            } catch (error) {
                console.error('Ошибка запроса:', error);
                alert('Произошла ошибка при запросе.');
            }
        });
    });

    // Функция для автоформатирования номера телефона
    function formatPhoneNumber(input) {
        let number = input.value.replace(/\D/g, '');

        if (number.length > 1) {
            number = '+7' + number.substring(1);
        }

        if (number.length > 12) {
            number = number.substring(0, 12);
        }

        input.value = number;
    }

    // Добавляем обработчик события input для поля телефона
    const phoneInput = document.querySelector('input[name="phone"]');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            formatPhoneNumber(this);
        });
    }
});
