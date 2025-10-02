# FastAPI Ecommerce

## Описание
Учебный проект интернет-магазина на FastAPI. Приложение демонстрирует организацию версионированного API, работу с Celery, WebSocket-соединениями и админ-панелью на базе FastAdmin.

## Основные возможности
- Версионированное API `/v1` с отдельными роутерами для товаров, категорий, отзывов и авторизации.
- Асинхронный доступ к PostgreSQL через SQLAlchemy 2.x (`asyncpg`).
- Выполнение фоновых задач в Celery с Redis в роли брокера и хранилища результатов.
- Админ-панель FastAdmin, смонтированная на `/admin`.
- WebSocket-соединение для трансляции сообщений всем подключённым клиентам.
- Набор middleware для логирования и измерения времени ответа.

## Структура проекта
```
fastapi_ecommerce/
├── AGENTS.md                # Описание архитектуры для ИИ-агента
├── README.md
├── requirements.txt
├── docker-compose.yml       # Локальная среда (web, db, redis, celery)
├── docker-compose.prod.yml  # Прод-конфигурация
├── nginx/                   # Конфигурация Nginx для прод-режима
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── main_routers.py      # Настройка подприложений и роутеров
│   ├── admin.py             # FastAdmin регистрация моделей
│   ├── backend/
│   │   ├── db.py            # Подключение к БД и базовый класс моделей
│   │   └── db_depends.py    # Зависимость для AsyncSession
│   ├── models/              # SQLAlchemy модели домена
│   ├── routers/
│   │   └── v1/              # Версионированные роутеры API
│   ├── schemas.py           # Pydantic-схемы
│   ├── tasks.py             # Celery-задачи
│   ├── templates/           # Jinja2-шаблоны `index.html`, `redirect.html`
│   └── ...                  # Middleware, менеджеры соединений и т. п.
├── app/prompts/             # Системные подсказки для ИИ-агента
└── prompts/tasks/           # Описания задач для генерации ответов
```
## Требования
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Установленные зависимости из `requirements.txt`

## Локальный запуск (без Docker)
1. Установите зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # или .venv\Scripts\activate на Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. Настройте переменные окружения (пример):
   ```bash
   export DATABASE_URL="postgresql+asyncpg://postgres_user:postgres_password@localhost:5432/postgres_database"
   export CELERY_BROKER_URL="redis://localhost:6379/0"
   export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
   ```
3. Примените миграции (если используется Alembic) или создайте схему вручную.
4. Запустите сервер разработки:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Для фоновых задач запустите Celery-воркер и, при необходимости, планировщик:
   ```bash
   celery -A app.main.celery worker --loglevel=info
   celery -A app.main.celery beat --loglevel=info
   ```
## Запуск через Docker Compose
```bash
docker compose up --build
```
Команда поднимет контейнеры приложения, PostgreSQL, Redis, Celery worker/beat и, при прод-конфигурации, Nginx. Проверьте переменные окружения в `docker-compose*.yml` перед запуском.

## Тестирование
В проекте отсутствуют автоматические тесты. Рекомендуется добавить Pytest и покрыть CRUD-операции и задачи Celery.

## Полезные ссылки
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Celery documentation](https://docs.celeryq.dev/)
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/en/20/)