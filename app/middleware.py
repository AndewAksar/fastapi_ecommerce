from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware


def add_middlewares(app: FastAPI):
    # Добавляем middleware для сессий
    app.add_middleware(SessionMiddleware, secret_key="secret-key-1234")

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
        allow_origins=origins,      # Разрешённые источники
        allow_credentials=True,     # Разрешить куки и авторизацию
        allow_methods=["*"],        # Разрешённые методы (GET, POST, PUT, DELETE и т.д.)
        allow_headers=["*"]         # Разрешённые заголовки
    )

    """
    # Настройка TrustedHostMiddleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["example.com", "*.example.com"])     # Разрешённые хосты
    """

    # Настройка GZipMiddleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)