# Календарь праздников мира (FastAPI + статика)

Сайт-календарь праздников на каждый день со всего мира.  
Бэкенд: FastAPI. Фронтенд: статический HTML/JS/CSS.  
Данные о праздниках берутся из публичного API [date.nager.at](https://date.nager.at).

## Структура

```
holiday-calendar/
├── app/
│   ├── main.py          # FastAPI приложение
│   └── static/
│       ├── index.html   # Фронтенд
│       ├── style.css    # Стили
│       └── app.js       # Логика календаря
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Запуск локально

```bash
# создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate

# установить зависимости
pip install -r requirements.txt

# запустить сервер
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Откройте http://localhost:8000

## Деплой через Docker

```bash
docker build -t holiday-calendar .
docker run -p 8000:8000 holiday-calendar
```

Откройте http://localhost:8000

## Деплой в облако (FastAPI / любой cloud с контейнерами)

Проект готов к деплою на любую платформу, поддерживающую Docker или Python:
- **Render** — подключите репозиторий, укажите Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Railway** — добавьте Dockerfile, Railway сам соберёт образ
- **Fly.io** — `fly launch` и `fly deploy`
- **Heroku** — добавьте `Procfile` с содержимым: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Переменная окружения `PORT` задаёт порт (по умолчанию 8000).

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Главная страница (статика) |
| GET | `/api/countries` | Список доступных стран |
| GET | `/api/holidays/{country_code}` | Праздники страны на год (`?year=2024`) |
| GET | `/api/holidays/{country_code}/{year}/{month}/{day}` | Праздники на конкретную дату |
| GET | `/api/holidays/today/{country_code}` | Праздники сегодня в выбранной стране |

## Особенности

- Календарь на выбранный месяц с подсветкой праздничных дней.
- Выбор страны и месяца.
- Показ деталей праздника по клику на дату.
- Автоматический фолбэк со списком стран, если внешний API недоступен.
- Готов к контейнеризации и деплою в облако.