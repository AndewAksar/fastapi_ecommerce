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
├── AGENTS.md                   # Описание архитектуры для ИИ-агента
├── README.md                   # Описание проекта
├── requirements.txt            # Завиисимости проекта
├── docker-compose.yml          # Локальная среда (web, db, redis, celery)
├── docker-compose.prod.yml     # Прод-конфигурация
├── nginx/                      # Конфигурация Nginx для прод-режима
├── app/
│   ├── main.py                 # Точка входа FastAPI
│   ├── main_routers.py         # Настройка подприложений и роутеров
│   ├── admin.py                # FastAdmin регистрация моделей
│   ├── backend/
│   │   ├── db.py               # Подключение к БД и базовый класс моделей
│   │   └── db_depends.py       # Зависимость для AsyncSession
│   ├── models/                 # SQLAlchemy модели домена
│   ├── routers/
│   │   └── v1/                 # Версионированные роутеры API
│   ├── schemas.py              # Pydantic-схемы
│   ├── tasks.py                # Celery-задачи
│   ├── templates/              # Jinja2-шаблоны `index.html`, `redirect.html`
│   └── ...                     # Middleware, менеджеры соединений и т. п.
├── app/prompts/                # Системные подсказки для ИИ-агента
└── prompts/tasks/              # Описания задач для генерации ответов
   └── self_prompt_template.md  # Шаблон самоинструкции перед кодовыми изменениями
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

### Ручной запуск Celery в Docker-контейнерах
Если необходимо перезапустить Celery отдельно от остальной инфраструктуры, используйте встроенные команды Compose:

```bash
docker compose run --rm celery_worker celery -A app.main.celery worker --loglevel=info
docker compose run --rm celery_beat celery -A app.main.celery beat --loglevel=info
```

Контейнер `web` получает переменные окружения для подключения к инфраструктуре по умолчанию:

- `DATABASE_URL=postgresql+asyncpg://postgres_user:postgres_password@db:5432/postgres_database`
- `CELERY_BROKER_URL=redis://redis:6379/0`
- `CELERY_RESULT_BACKEND=redis://redis:6379/0`

При необходимости переопределите их в `.env` или через параметры запуска `docker compose`.

## Использование self_prompt_template
- Перед каждым запросом на генерацию или изменение кода агент обязан заполнить файл `prompts/tasks/self_prompt_template.md`,
  зафиксировав контекст, цель, запланированные шаги и историю итераций.
- Для каждой итерации следует копировать раздел «Итерация N», заменяя `N` на номер итерации и последовательно заполняя блоки
  «Запрос», «План», «Результат» и «Выводы».
- Заполненный шаблон должен сопровождать кодовые изменения и использоваться как отправная точка для анализа прогресса.

## Тестирование
В проекте отсутствуют автоматические тесты. Рекомендуется добавить Pytest и покрыть CRUD-операции и задачи Celery.

## Пагинация и фильтры в списках товаров и отзывов
Эндпоинты `/v1/products/`, `/v1/products/{category_slug}`, `/v1/reviews/` и `/v1/reviews/{product_slug}`
поддерживают единый набор query-параметров для пагинации и фильтрации:

| Параметр   | Тип   | Значение по умолчанию | Описание |
|------------|-------|-----------------------|----------|
| `limit`    | int   | 10                    | Максимальное количество элементов в выдаче. Допустимые значения: 1..100. |
| `offset`   | int   | 0                     | Смещение относительно начала списка. |
| `search`   | str   | `null`                | Поиск по названию и описанию товара или по тексту отзыва. |
| `min_price`| int   | `null`                | Нижняя граница цены товара. |
| `max_price`| int   | `null`                | Верхняя граница цены товара. |

Пример запроса на получение товаров категории с фильтрами:

```http
GET /v1/products/smartphones?limit=5&offset=5&search=pro&min_price=1000&max_price=5000
```

Ответы перечисленных эндпоинтов имеют структуру:

```json
{
  "items": [
    { "id": 1, "name": "Example", "price": 1234, "slug": "example", "rating": 4.5, "is_active": true, ... }
  ],
  "total": 42,
  "limit": 5,
  "offset": 5
}
```

- Поле `items` всегда возвращает список (даже если он пуст), что позволяет фронтенду обрабатывать «пустые» выборки без ошибки.
- `total` отражает общее количество записей до применения `limit/offset`.

Аналогичные параметры работают и для списка отзывов, при этом фильтр `search` ищет по тексту комментария, а диапазон цен
учитывает стоимость связанного товара. Для выборки отзывов конкретного товара (`/v1/reviews/{product_slug}`) ценовые фильтры
используются для проверки соответствия самого товара — при несоблюдении диапазона API вернёт пустой список.

## Полезные ссылки
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Celery documentation](https://docs.celeryq.dev/)
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/en/20/)

## Журнал изменений ИИ-агента

Для отслеживания правок, выполненных ИИ-агентами, используйте файл [AI_CHANGELOG.md](AI_CHANGELOG.md). После каждого коммита или pull request, выполненного агентом, добавляйте новую запись по описанному в файле формату.