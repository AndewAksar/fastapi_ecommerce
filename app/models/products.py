from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.backend.db import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    slug = Column(String(100), unique=True, index=True)
    description = Column(String(200))
    image_url = Column(String(100))
    price = Column(Integer)
    stock = Column(Integer)
    category_id = Column(Integer, ForeignKey("categories.id"))
    rating = Column(Float)
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products", uselist=False)