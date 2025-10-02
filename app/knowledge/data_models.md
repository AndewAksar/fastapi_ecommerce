# Доменные модели

Документ описывает основные ORM-сущности и их связи. Все модели унаследованы от `app.backend.db.Base` и используют SQLAlchemy 2.x с асинхронными сессиями.

## User (`app/models/user.py`)
| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | `Integer`, PK | Уникальный идентификатор пользователя. |
| `first_name`, `last_name` | `String` | Имя и фамилия. |
| `username` | `String`, unique | Уникальный логин для авторизации. |
| `email` | `String`, unique | Email пользователя. |
| `hashed_password` | `String` | Пароль в хэшированном виде (`passlib[bcrypt]`). |
| `is_active` | `Boolean` | Статус активности. |
| `is_admin` | `Boolean` | Флаг администратора. |
| `is_supplier` | `Boolean` | Флаг поставщика (продавца). |
| `is_customer` | `Boolean` | Флаг покупателя, по умолчанию `True`. |

**Использование:** роли определяют доступ к эндпоинтам (`permission.py`, `products.py`). Пароль должен храниться с использованием `bcrypt_context`.

## Category (`app/models/category.py`)
| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | `Integer`, PK | Идентификатор категории. |
| `name` | `String` | Название категории. |
| `slug` | `String`, unique | Слаг, используется в URL. |
| `is_active` | `Boolean` | Флаг активности. |
| `parent_id` | `Integer`, FK -> `categories.id` | Родительская категория, `NULL` для корня. |

**Связи:** `products = relationship("Product", back_populates="category")`.

**Особенности:** файл содержит `print(CreateTable(...))` для отладки — при миграциях уберите, чтобы избежать шума в логах.

## Product (`app/models/products.py`)
| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | `Integer`, PK | Идентификатор товара. |
| `name` | `String` | Название. |
| `slug` | `String`, unique | Слаг для URL. Формируется через `slugify`. |
| `description` | `String` | Описание товара. |
| `price` | `Integer` | Цена в условных единицах (целое). |
| `image_url` | `String` | Ссылка на изображение. |
| `stock` | `Integer` | Остаток на складе. |
| `supplier_id` | `Integer`, FK -> `users.id` | Пользователь, разместивший товар. |
| `category_id` | `Integer`, FK -> `categories.id` | Категория товара. |
| `rating` | `Float`, default 0.0 | Средний рейтинг. |
| `is_active` | `Boolean`, default True | Статус публикации. |

**Связи:** `category = relationship('Category', back_populates='products')`. Обратная связь с отзывами не определена — агрегирование рейтинга делается вручную.

## Review (`app/models/reviews.py`)
| Поле | Тип | Назначение |
| --- | --- | --- |
| `id` | `Integer`, PK | Идентификатор отзыва. |
| `user_id` | `Integer`, FK -> `users.id` | Автор отзыва. |
| `product_id` | `Integer`, FK -> `products.id` | Товар. |
| `comment` | `String` | Текст отзыва. |
| `comment_date` | `DateTime`, default `func.now()` | Дата создания. |
| `grade` | `Float` | Оценка от 1 до 5. |
| `is_active` | `Boolean`, default True | Флаг активности. |

**Особенности:** модуль содержит многострочный docstring, описывающий поля. Валидация оценки реализована на уровне Pydantic-схемы.

## Schema объекты (`app/schemas.py`)
- `CreateProduct`, `CreateCategory`, `CreateUser`, `CreateReview` — Pydantic-модели для входящих данных.
- `ProductRead` и `ReviewRead` используются для сериализации отдельных сущностей в ответах.
- `ProductListResponse` и `ReviewListResponse` оборачивают списки с полями `items`, `total`, `limit`, `offset`. Эти схемы обязательны для публичных списков товаров и отзывов, чтобы фронтенд мог строить пагинацию.
- `CreateReview.grade` ограничен через `confloat(ge=1, le=5)` и дополнительный валидатор. Метод `validate_grade` обязан возвращать исходное значение `grade`.

## Celery и вспомогательные структуры
- Celery-задачи объявлены в `app/tasks.py` и используют строковые сообщения; возвращаемый объект — словарь со статусом.
- Менеджер веб-сокетов (`app/connection_manager.py`) хранит активные `WebSocket`-подключения и транслирует сообщения всем клиентам.

## Схема БД в целом
```
User 1<--->* Product (через `supplier_id`)
User 1<--->* Review
Category 1<--->* Product
Category (parent_id) реализует древовидную структуру (adjacency list).
Product 1<--->* Review
```

При добавлении новых моделей сохраняйте единый стиль именования, добавляйте внешние ключи и обновляйте данный документ.
