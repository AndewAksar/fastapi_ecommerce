from pydantic import BaseModel, confloat, validator

class CreateProduct(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    stock: int
    category: int

class CreateCategory(BaseModel):
    name: str
    parent_id: int | None = None

class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

"""
Класс для создания отзыва, включает в себя следующие поля:
    user_id: числовое поле
    product_id: числовое поле
    comment: текстовое поле
    grade: числовое поле
    is_active: логическое поле
"""
class CreateReview(BaseModel):
    user_id: int
    product_id: int
    comment: str = None
    grade: confloat(ge=1, le=5)
    is_active: bool = True

    @validator('grade')
    def validate_grade(cls, grade):
        if not (1 <= grade <= 5):
            raise ValueError('The rating must be between 1 and 5.')
        return grade