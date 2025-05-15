from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.gzip import GZipMiddleware
import os

from app.routers.v1 import auth, category, permission, products, reviews

# Создаём основное приложение
app = FastAPI(
    title="FastAPI Ecommerce App",
    version="1.0.0",
    description="Ecommerce API with versioning",
    servers=[
        {"url": "/v1", "description": "Version 1"}
    ]
)

# Создаём подприложение для версии v1
app_v1 = FastAPI()

# Монтируем статические файлы из директории 'static' по пути '/static'
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка шаблонизатора Jinja2
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Определяем маршрут приветствия для основного приложения
@app.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    return templates.TemplateResponse("test_cors.html", {"request": request})

# Добавляем маршруты к подприложению v1
app_v1.include_router(category.router)
app_v1.include_router(products.router)
app_v1.include_router(auth.router)
app_v1.include_router(permission.router)
app_v1.include_router(reviews.router)

# Монтируем подприложения к основному приложению
app.mount('/v1', app_v1)

# Добавляем HTTPSRedirectMiddleware (только в продакшн-среде)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Настройка CORS
origins = [
    "https://example.com"
]

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Разрешённые источники
    allow_credentials=True,         # Разрешить куки и авторизацию
    allow_methods=["*"],            # Разрешённые методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"]             # Разрешённые заголовки
)

# Настройка TrustedHostMiddleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"])     # Разрешённые хосты

# Настройка GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Запуск приложения (если запускаем как скрипт)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)