from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.websockets import WebSocketDisconnect
from celery import Celery
import os
from fastadmin import fastapi_app as admin_app

from app.connection_manager import ConnectionManager
from app.logging_config import configure_logging, log_middleware
from app.main_routers import setup_routers
from app.middleware import add_middlewares
from app.timing import TimingMiddleWare



# Определяем путь к директории шаблонов
templates_dir = os.path.join(os.path.dirname(__file__), "templates")


# Создаём экземпляр Jinja2Templates с указанным путём к директории шаблонов
templates = Jinja2Templates(directory=templates_dir)


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

# регистрация приложения админки
app.mount("/admin", admin_app)

# Создаем экземпляр Celery
celery = Celery(
    'main',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    broker_connection_retry_on_startup=True
)


# Настройка расписания задач для Celery
celery.conf.beat_schedule = {
    'run-me-background-task': {
        'task': 'app.tasks.call_background_task',
        'schedule': 6.0,
        'args': ('Test text message',)
    }
}


# Автоматическое обнаружение задач в модулях 'tasks'
celery.autodiscover_tasks(['app.tasks'])


# Создаем экземпляр ConnectionManager
manager = ConnectionManager()


# Добавляем middleware для измерения времени выполнения запроса
app.add_middleware(TimingMiddleWare)


# Добавляем middleware для логирования
app.middleware("http")(log_middleware)


# Настройка middleware
add_middlewares(app)


# Настройка маршрутов
setup_routers(app)


# Маршрут для корневого пути с использованием Jinja2Templates
@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Добавляем маршрут для корневого пути с кнопкой для редиректа (перехода на) /v1/
@app.get("/redirect", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("redirect.html", {"request": request})


# Добавления локального веб-сокета
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect as e:
        manager.connections.remove(websocket)
        print(f"Connection closed. Error: {e.code}")


# Запуск приложения (если запускаем как скрипт)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)