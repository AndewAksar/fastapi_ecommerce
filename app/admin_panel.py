from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, ValidationError, constr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.user import User

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secret"
SESSION_COOKIE_NAME = "admin_session"
SESSION_TOKEN = "basic-admin-session"

_templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

router = APIRouter(prefix="/admin", tags=["Admin"], include_in_schema=False)

strict_basic = HTTPBasic()
optional_basic = HTTPBasic(auto_error=False)
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserBase(BaseModel):
    first_name: constr(strip_whitespace=True, min_length=1, max_length=50)
    last_name: constr(strip_whitespace=True, min_length=1, max_length=50)
    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False
    is_supplier: bool = False
    is_customer: bool = True

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: constr(min_length=6, max_length=128)


class UserUpdate(UserBase):
    password: constr(min_length=6, max_length=128) | None = None


@dataclass
class AdminAuth:
    method: str


def _credentials_valid(credentials: HTTPBasicCredentials) -> bool:
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    return correct_username and correct_password


def _checkbox_to_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() == "true"


def _to_namespace(data: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(**data)


def _humanize_errors(error: ValidationError) -> list[str]:
    messages: list[str] = []
    for item in error.errors():
        location = " → ".join(str(part) for part in item["loc"])
        messages.append(f"{location}: {item['msg']}")
    return messages


async def _fetch_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


async def _render_users_page(
    *,
    request: Request,
    db: AsyncSession,
    errors: list[str] | None = None,
    message: str | None = None,
    form_data: SimpleNamespace | None = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    users = await _fetch_users(db)
    context = {
        "request": request,
        "users": users,
        "errors": errors or [],
        "message": message,
        "form_data": form_data,
    }
    return templates.TemplateResponse("admin/users.html", context, status_code=status_code)


def require_basic_login(
    credentials: HTTPBasicCredentials = Depends(strict_basic),
) -> AdminAuth:
    if not _credentials_valid(credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные администратора.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return AdminAuth(method="basic")


def ensure_admin(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(optional_basic),
) -> AdminAuth:
    if credentials is not None:
        if not _credentials_valid(credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учётные данные администратора.",
                headers={"WWW-Authenticate": "Basic"},
            )
        return AdminAuth(method="basic")

    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token == SESSION_TOKEN:
        return AdminAuth(method="cookie")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется авторизация администратора.",
        headers={"WWW-Authenticate": "Basic"},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    context = {"request": request, "errors": [], "message": None}
    return templates.TemplateResponse("admin/login.html", context)


@router.post("/login")
async def login(_: AdminAuth = Depends(require_basic_login)) -> JSONResponse:
    response = JSONResponse({"detail": "ok"})
    response.set_cookie(
        SESSION_COOKIE_NAME,
        SESSION_TOKEN,
        httponly=True,
        samesite="lax",
        max_age=3600,
    )
    return response


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    _: AdminAuth = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    message = request.query_params.get("message")
    return await _render_users_page(request=request, db=db, message=message)


@router.post("/users")
async def create_user(
    request: Request,
    _: AdminAuth = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_active: str | None = Form(None),
    is_admin: str | None = Form(None),
    is_supplier: str | None = Form(None),
    is_customer: str | None = Form(None),
):
    form_values = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": email,
        "password": password,
        "is_active": _checkbox_to_bool(is_active, default=True),
        "is_admin": _checkbox_to_bool(is_admin),
        "is_supplier": _checkbox_to_bool(is_supplier),
        "is_customer": _checkbox_to_bool(is_customer, default=True),
    }

    try:
        payload = UserCreate(**form_values)
    except ValidationError as exc:
        safe_values = form_values.copy()
        safe_values.pop("password", None)
        return await _render_users_page(
            request=request,
            db=db,
            errors=_humanize_errors(exc),
            form_data=_to_namespace(safe_values),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        email=payload.email,
        hashed_password=password_context.hash(payload.password),
        is_active=payload.is_active,
        is_admin=payload.is_admin,
        is_supplier=payload.is_supplier,
        is_customer=payload.is_customer,
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        safe_values = form_values.copy()
        safe_values.pop("password", None)
        return await _render_users_page(
            request=request,
            db=db,
            errors=["Логин или email уже используются."],
            form_data=_to_namespace(safe_values),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/admin/users?message=Пользователь создан",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user(
    request: Request,
    user_id: int,
    _: AdminAuth = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")

    context = {
        "request": request,
        "user": user,
        "errors": [],
        "message": None,
        "form_data": None,
    }
    return templates.TemplateResponse("admin/user_form.html", context)


@router.post("/users/{user_id}")
async def update_user(
    request: Request,
    user_id: int,
    _: AdminAuth = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str | None = Form(None),
    is_active: str | None = Form(None),
    is_admin: str | None = Form(None),
    is_supplier: str | None = Form(None),
    is_customer: str | None = Form(None),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")

    cleaned_password = password or None

    form_values = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": email,
        "password": cleaned_password,
        "is_active": _checkbox_to_bool(is_active),
        "is_admin": _checkbox_to_bool(is_admin),
        "is_supplier": _checkbox_to_bool(is_supplier),
        "is_customer": _checkbox_to_bool(is_customer),
    }

    try:
        payload = UserUpdate(**form_values)
    except ValidationError as exc:
        context = {
            "request": request,
            "user": user,
            "errors": _humanize_errors(exc),
            "message": None,
            "form_data": _to_namespace({
                key: value for key, value in form_values.items() if key != "password"
            }),
        }
        return templates.TemplateResponse(
            "admin/user_form.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.username = payload.username
    user.email = payload.email
    user.is_active = payload.is_active
    user.is_admin = payload.is_admin
    user.is_supplier = payload.is_supplier
    user.is_customer = payload.is_customer

    if payload.password:
        user.hashed_password = password_context.hash(payload.password)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        context = {
            "request": request,
            "user": user,
            "errors": ["Логин или email уже используются."],
            "message": None,
            "form_data": _to_namespace({
                key: value for key, value in form_values.items() if key != "password"
            }),
        }
        return templates.TemplateResponse(
            "admin/user_form.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/admin/users?message=Изменения сохранены",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    _: AdminAuth = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.")

    await db.delete(user)
    await db.commit()

    return RedirectResponse(
        url="/admin/users?message=Пользователь удалён",
        status_code=status.HTTP_303_SEE_OTHER,
    )
