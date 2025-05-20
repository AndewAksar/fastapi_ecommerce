from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from celery import Celery
from fastapi.templating import Jinja2Templates
import os

from app.logging_config import configure_logging, log_middleware
from app.main_routers import setup_routers
from app.middleware import add_middlewares
from app.timing import TimingMiddleWare


# Настройка логирования
configure_logging()

# Создаём основное приложение
app = FastAPI(
    title="FastAPI Ecommerce App",
    version="1.0.0",
    description="Ecommerce API with versioning",
    servers=[
        {"url": "/", "description": "Root Server"},
        {"url": "/v1", "description": "Version 1"}
    ]
)

# Настройка Celery с использованием Redis в качестве брокера
celery = Celery(
    __name__,
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    broker_connection_retry_on_startup=True
)


# Автоматическое обнаружение задач в модулях 'tasks'
celery.autodiscover_tasks(['app.tasks'])

# Добавляем middleware для измерения времени выполнения запроса
app.add_middleware(TimingMiddleWare)

# Добавляем middleware для логирования
app.middleware("http")(log_middleware)

# Настройка middleware
add_middlewares(app)

# Настройка маршрутов
setup_routers(app)

# Редирект с корневого пути на /v1/
# Добавляем маршрут для корневого пути с кнопкой для перехода на /v1/
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = Jinja2Templates(directory=templates_dir)
    return templates.TemplateResponse("redirect.html", {"request": request})


# Запуск приложения (если запускаем как скрипт)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)