document.getElementById('goButton').addEventListener('click', async function() {
    try {
        const response = await fetch('/get_random', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const result = await response.json();
        const goButton = document.getElementById('goButton');
        const addLink = document.getElementById('addLink');
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
                goButton.style.display = 'inline-block'; // Показываем кнопку по центру
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
