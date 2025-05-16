from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.routers.v1 import auth, category, permission, products, reviews


def setup_routes(app: FastAPI):
    # Монтируем статические файлы из директории 'static' по пути '/static'
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Настройка шаблонизатора Jinja2
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = Jinja2Templates(directory=templates_dir)

    # Определяем маршрут приветствия для основного приложения
    @app.get("/", response_class=HTMLResponse)
    async def welcome(request: Request):
        return templates.TemplateResponse("test_cors.html", {"request": request})

    # Создаём подприложение для версии v1
    app_v1 = FastAPI()

    # Добавляем маршруты к подприложению v1
    app_v1.include_router(category.router)
    app_v1.include_router(products.router)
    app_v1.include_router(auth.router)
    app_v1.include_router(permission.router)
    app_v1.include_router(reviews.router)

    # Монтируем подприложения к основному приложению
    app.mount('/v1', app_v1)