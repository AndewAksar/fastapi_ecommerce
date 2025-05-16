from fastapi import FastAPI

from app.logging_config import configure_logging, log_middleware
from app.routes import setup_routes
from app.middleware import add_middlewares


# Настройка логирования
configure_logging()

# Создаём основное приложение
app = FastAPI(
    title="FastAPI Ecommerce App",
    version="1.0.0",
    description="Ecommerce API with versioning",
    servers=[
        {"url": "/v1", "description": "Version 1"}
    ]
)

# Добавляем middleware для логирования
app.middleware("http")(log_middleware)

# Настройка middleware
add_middlewares(app)

# Настройка маршрутов
setup_routes(app)


# Запуск приложения (если запускаем как скрипт)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)