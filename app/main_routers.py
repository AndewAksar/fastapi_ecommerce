from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.routers.v1 import auth, category, permission, products, reviews, session
from app.tasks import call_background_task


def setup_routers(app: FastAPI):
    # Настройка шаблонизатора Jinja2
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = Jinja2Templates(directory=templates_dir)

    # Создаём подприложение для версии v1
    app_v1 = FastAPI()

    # Запуск асинхронной задачи Celery
    @app_v1.get("/")
    async def hello_world(message: str = None):
        call_background_task.delay(message)
        return {'message': f'Hello World! {message}'}

    # Добавляем маршруты к подприложению v1
    app_v1.include_router(category.router)
    app_v1.include_router(products.router)
    app_v1.include_router(auth.router)
    app_v1.include_router(permission.router)
    app_v1.include_router(reviews.router)
    app_v1.include_router(session.router)

    # Монтируем подприложения к основному приложению
    app.mount('/v1', app_v1)

    # Определяем маршрут для корневого пути с кнопкой для перехода на /v1/
    @app.get("/redirect", response_class=HTMLResponse)
    async def redirect_to_v1(request: Request):
        return templates.TemplateResponse("redirect.html", {"request": request})