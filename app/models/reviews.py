from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.backend.db import Base
from app.models.user import User
from app.models.products import Product

"""
класс модели отзывов, принимающих в себя поля: 
    id: Числовое поле, являющееся первичным ключом.
    user_id: Поле связи с таблицей пользователей.
    product_id: Поле связи с таблицей товара.
    comment: Текстовое поле отзыва о товаре, может быть пустым.
    comment_date: Поле даты отзыва, по умолчанию заполняется автоматически.
    grade: Числовое поле оценки товара(рейтинг).
    is_active: Булево поле, по умолчанию True.
"""
class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    comment = Column(String)
    comment_date = Column(DateTime, default=func.now(), nullable=False)
    grade = Column(Float)
    is_active = Column(Boolean, default=True)



