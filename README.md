# FastAPI Ecommerce

Учебный проект интернет-магазина на FastAPI. Приложение демонстрирует работу с асинхронным PostgreSQL, Celery, WebSocket-уведомлениями и административной панелью FastAdmin. Репозиторий подготовлен как песочница для изучения архитектуры и онбординга новых разработчиков/ИИ-агентов.

## Ключевые возможности
- Версионированное API `/v1` с отдельными роутерами для категорий, товаров, отзывов, сессий и авторизации.
- Асинхронный доступ к БД через SQLAlchemy 2.x (`asyncpg`).
- Аутентификация по JWT и ролевое разграничение (`admin`, `supplier`, `customer`).
- Фоновые задачи в Celery с Redis в роли брокера и стореджа результатов.
- Админ-панель FastAdmin, смонтированная на `/admin`.
- WebSocket-подключения для широковещательных уведомлений.

## Технологический стек
- Python 3.11+
- FastAPI, Starlette, Pydantic v1 (готовность к миграции на v2)
- SQLAlchemy 2.x (async), asyncpg
- Celery + Redis
- FastAdmin
- Docker / Docker Compose

## Структура проекта
```
fastapi_ecommerce/
├── AGENTS.md                   # Глобальное руководство для ИИ-агента
├── README.md
├── requirements.txt
├── docker-compose.yml          # Локальная среда (web, db, redis, celery)
├── docker-compose.prod.yml     # Прод-конфигурация (web, db, redis, celery, nginx)
├── nginx/                      # Nginx-конфигурация для прод-режима
├── app/
│   ├── main.py                 # Точка входа FastAPI
│   ├── main_routers.py         # Регистрация версий API и вспомогательных сервисов
│   ├── admin.py                # FastAdmin инициализация
│   ├── backend/                # Работа с базой (engine, зависимости)
│   ├── models/                 # SQLAlchemy-модели домена
│   ├── routers/v1/             # Версионированные роутеры API
│   ├── schemas.py              # Pydantic-схемы запросов
│   ├── tasks.py                # Celery-задачи
│   ├── templates/              # Jinja2-шаблоны (`index.html`, `redirect.html`)
│   ├── knowledge/              # База знаний (эндпоинты, модели, соглашения)
│   └── ...                     # Middleware, менеджер WebSocket и др.
├── app/prompts/                # Системные подсказки для ИИ-агента
└── prompts/tasks/              # Задания для ИИ-агента (генерация кода, ревью и т. п.)
```

Дополнительные документы:
- `app/knowledge/endpoints.md` — описание всех маршрутов и их особенностей.
- `app/knowledge/data_models.md` — схема доменных моделей и их связи.
- `app/knowledge/conventions.md` — инженерные соглашения по работе с кодовой базой.

## Подготовка окружения
### Переменные окружения
Перед запуском убедитесь, что заданы:
- `DATABASE_URL` — строка подключения PostgreSQL (пример: `postgresql+asyncpg://user:password@localhost:5432/db`).
- `CELERY_BROKER_URL` — адрес брокера Redis (`redis://localhost:6379/0`).
- `CELERY_RESULT_BACKEND` — хранилище результатов (`redis://localhost:6379/0`).
- `SECRET_KEY` — ключ подписи JWT (в коде есть значение по умолчанию, рекомендуется переопределить).

Секреты можно хранить в `.env` и подключать через менеджер конфигурации (не реализовано из коробки).

### Локальный запуск (uvicorn)
```bash
python -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows
pip install --upgrade pip
pip install -r requirements.txt

# Задайте переменные окружения (см. выше)
uvicorn app.main:app --reload
```

Для Celery в отдельном терминале:
```bash
celery -A app.main.celery worker --loglevel=info
celery -A app.main.celery beat --loglevel=info  # по желанию
```

### Запуск через Docker Compose
```bash
docker compose up --build
```

Команда поднимет приложение, PostgreSQL, Redis, Celery worker/beat и (в прод-режиме) Nginx. Проверьте переменные окружения и volume в `docker-compose*.yml` перед запуском.

## Тестирование
Автоматические тесты в репозитории отсутствуют. Рекомендуется добавить `pytest`/`pytest-asyncio`, фикстуры для `AsyncSession` и покрыть CRUD-операции, авторизацию и Celery-задачи.

## Известные ограничения
- Конфигурация БД, Redis и JWT секрет захардкожены в коде и требуют выноса в настройки.
- Роутеры возвращают ORM-объекты без `response_model`, что затрудняет сериализацию.
- В `app/models/category.py` присутствует отладочный вывод DDL через `print`.
- В некоторых обработчиках используются `db.scalars(...)` без извлечения единственного объекта — учитывайте при добавлении логики.
- Нет миграций и инструментов для управления схемой БД.

## Полезные ссылки
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Celery documentation](https://docs.celeryq.dev/)
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/en/20/)

При доработке обновляйте README и документы из `app/knowledge/`, чтобы сохранять актуальный контекст для команды.
