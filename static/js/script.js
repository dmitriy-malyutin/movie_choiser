document.addEventListener('DOMContentLoaded', () => {
    console.log("Страница загружена, инициализация скрипта.");

    const goButton = document.getElementById('goButton');
    const resultDiv = document.getElementById('result');
    const phoneInput = document.querySelector('input[name="phone"]');


    goButton.addEventListener('click', async () => {
        resultDiv.innerHTML = '';
        goButton.style.display = 'none';

        try {
            const response = await fetch('/get_random_entry', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            });

            if (!response.ok) throw new Error('Не удалось получить данные.');
            const result = await response.json();

            if (result.name && result.word) {
                resultDiv.innerHTML = `
                    <div style="font-size: 24px;">Победитель: ${result.name}</div>
                    <div style="font-size: 24px;">Фильм: ${result.word}</div>
                    <div>
                        <button id="deleteButton">Просмотрено, удалить</button>
                        <button id="replayButton">Переиграть</button>
                    </div>
                `;

                document.getElementById('deleteButton').addEventListener('click', () => deleteEntry(result));
                document.getElementById('replayButton').addEventListener('click', () => goButton.click());
            } else {
                resultDiv.innerText = 'Не добавлено ни одной записи, хотите добавить?';
                goButton.style.display = 'inline-block';
            }
        } catch (error) {
            console.error('Ошибка при получении случайной записи:', error);
            resultDiv.innerText = 'Произошла ошибка при получении данных.';
            goButton.style.display = 'inline-block';
        }
    });

    const deleteEntry = async ({ name, word }) => {
        try {
            const response = await fetch('/delete_entry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, word }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Ошибка при удалении записи.');
            }
            resultDiv.innerText = 'Фильм удален.';
            goButton.style.display = 'inline-block';
        } catch (error) {
            console.error('Ошибка при удалении:', error);
            alert(error.message);
        }
    };

    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const name = button.getAttribute('data-name');
            const word = button.getAttribute('data-word');
            await deleteEntry({ name, word });
            button.closest('tr')?.remove();
            alert('Запись удалена.');
        });
    });

    const formatPhoneNumber = (input) => {
        let number = input.value.replace(/\D/g, '');
        number = number.length > 1 ? `+7${number.slice(1, 12)}` : number;
        input.value = number;
    };

    phoneInput?.addEventListener('input', () => formatPhoneNumber(phoneInput));
});
