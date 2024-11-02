# movie_choiser


## Приложение для выбора фильма

1. Составляете список фильмов
2. Рандомайзер выбирает один из списка

## Окружение
Postgres любой версии

[Python libs](requirements.txt)
## Запуск
В корень положить файлик connections.json
```json
{
    "moovie_chooser": {
        "postgres" : {
            "host" : "host",
            "port" : 5432,
            "db" : "db",
            "user" : "user",
            "password": "password"
        }
    }, "secret_key" : "secret_key"
}
```

И запустить

```bash
python app.py
```


