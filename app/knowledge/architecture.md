# Архитектура приложения

Документ описывает ключевые компоненты FastAPI Ecommerce и их взаимодействие. Используйте его как шпаргалку при онбординге и планировании изменений.

## Обзор модулей
- `app/main.py` — создаёт экземпляр FastAPI, подключает middleware, Celery и роутеры.
- `app/main_routers.py` — монтирует версию API `/v1` и объединяет модули из `app.routers.v1`.
- `app/backend/` — инициализация БД (SQLAlchemy Async), зависимости для сессий, вспомогательные утилиты.
- `app/models/` — ORM-сущности: `User`, `Category`, `Product`, `Review`, `Permission`.
- `app/schemas.py` — Pydantic-модели для запросов и ответов.
- `app/services/` — бизнес-логика (валидация, агрегации, фоновые задачи).
- `app/tasks.py` — Celery-задачи и планировщик.
- `app/admin.py` и `app/templates/` — административный UI и HTML-шаблоны.
- `app/connection_manager.py` — управление WebSocket-подключениями.

## Потоки данных
```
[Client]
   |
   v
FastAPI Router (app.routers.v1.*)
   |
   v
Service / Use Case (app.services.*)
   |
   v
Repository & Session (app.backend.db_depends -> AsyncSession)
   |
   v
PostgreSQL
```

- Ответы возвращаются через Pydantic-схемы (`app.schemas`).
- Логирование и метрики проходят через `TimingMiddleware` и конфигурацию `app.logging_config`.

## Фоновые и интеграционные потоки
```
FastAPI Endpoint --enqueue--> Celery Task (app.tasks.call_background_task)
                                    |
                                    v
                                 Redis (broker)
                                    |
                                    v
                               Celery Worker
                                    |
                                    v
                                 PostgreSQL / внешние сервисы
```

- Планировщик Celery Beat периодически ставит задачи без участия клиента.
- WebSocket-уведомления рассылаются через `ConnectionManager.broadcast` всем активным сессиям.

## Точки расширения
- Добавляйте новые версии API в `app/main_routers.py`, создавая подприложения с собственными зависимостями.
- Для новых сущностей определяйте ORM-модель, схему в `app/schemas.py` и сервис с чистой бизнес-логикой.
- Общие зависимости (кэш, настройки) выносите в `app/dependencies.py`, а конфигурацию — в Pydantic Settings.
