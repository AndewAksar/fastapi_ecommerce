import typing as tp
import uuid

import bcrypt
from sqlalchemy import Boolean, Integer, String, Text, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fastadmin import SqlAlchemyModelAdmin, register

from app.models.user import User
from app.backend.db import async_session_maker


@register(User, sqlalchemy_sessionmaker=async_session_maker)
class UserAdmin(SqlAlchemyModelAdmin):
    exclude = ("hashed_password",)
    list_display = ("id", "username", "is_admin", "is_active")
    list_display_links = ("id", "username")
    list_filter = ("id", "username", "is_admin", "is_active")
    search_fields = ("username",)

    async def authenticate(self, username: str, password: str) -> uuid.UUID | int | None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            query = select(self.model_cls).filter_by(username=username, is_admin=True)
            result = await session.scalars(query)
            obj = result.first()
            if not obj:
                return None
            if not bcrypt.checkpw(password.encode(), obj.hashed_password.encode()):
                return None
            return obj.id

    async def change_password(self, id: uuid.UUID | int, password: str) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            query = update(self.model_cls).where(User.id.in_([id])).values(hashed_password=hashed_password)
            await session.execute(query)
            await session.commit()

    async def orm_save_upload_field(self, obj: tp.Any, field: str, base64: str) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            # convert base64 to bytes, upload to s3/filestorage, get url and save or save base64 as is to db (don't recomment it)
            query = update(self.model_cls).where(User.id.in_([obj.id])).values(**{field: base64})
            await session.execute(query)
            await session.commit()