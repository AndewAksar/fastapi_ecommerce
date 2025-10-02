from typing import Sequence

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.settings import settings


def add_middlewares(
    app: FastAPI,
    *,
    cors_origins: Sequence[str] | None = None,
    session_secret: str | None = None,
) -> None:
    # Добавляем middleware для сессий
    app.add_middleware(SessionMiddleware, secret_key=session_secret or settings.session_secret)

    # Добавляем HTTPSRedirectMiddleware (только в продакшн-среде)
    if os.getenv("ENVIRONMENT") == "production":
        app.add_middleware(HTTPSRedirectMiddleware)

    # Настройка CORS
    origins = list(cors_origins or settings.cors_origins)

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