from datetime import datetime

from pydantic import BaseModel, confloat, validator


class CreateProduct(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    stock: int
    category: int


class ProductRead(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    price: int
    image_url: str
    stock: int
    supplier_id: int | None
    category_id: int
    rating: float
    is_active: bool

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Список товаров с метаинформацией для пагинации."""

    items: list[ProductRead]
    total: int
    limit: int
    offset: int


class CreateCategory(BaseModel):
    name: str
    parent_id: int | None = None


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    parent_id: int | None

    class Config:
        from_attributes = True


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


class CreateReview(BaseModel):
    product_id: int
    comment: str | None = None
    grade: confloat(ge=1, le=5)
    is_active: bool = True

    @validator("grade")
    def validate_grade(cls, grade: float) -> float:
        if not (1 <= grade <= 5):
            raise ValueError("The rating must be between 1 and 5.")
        return grade


class ReviewRead(BaseModel):
    id: int
    user_id: int | None
    product_id: int | None
    comment: str | None
    comment_date: datetime
    grade: float
    is_active: bool

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Список отзывов с данными о пагинации."""

    items: list[ReviewRead]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    status_code: int
    transaction: str

    class Config:
        from_attributes = True