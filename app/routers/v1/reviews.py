from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, func
from typing import Annotated

from app.routers.v1.auth import get_current_user
from app.backend.db_depends import get_db
from app.models.reviews import Review
from app.models.products import Product
from app.schemas import CreateReview

router = APIRouter(prefix="/reviews", tags=["reviews"])


# Получение полного перечня отзывов. Разрешен доступ всем.
@router.get("/")
async def all_reviews(db: AsyncSession = Depends(get_db)):
    reviews = await db.scalars(select(Review).where(Review.is_active == True))
    return reviews.all()

# Получение отзывов по слагу товара. Разрешен доступ всем.
@router.get("/{product_slug}")
async def products_reviews(product_slug: str, db: AsyncSession = Depends(get_db)):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )
    else:
        reviews = await db.scalars(select(Review).where(Review.product_id == product.id, Review.is_active == True))
        if reviews is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found!"
            )
        else:
            return reviews.all()

# Добавление отзыва. Разрешен доступ только авторизованным пользователям.
@router.post("/")
async def add_review(
        db: Annotated[AsyncSession, Depends(get_db)],
        create_review: CreateReview,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user:
        product = await db.scalar(select(Product).where(Product.id == create_review.product_id))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found!"
            )
        else:
            # Проверка наличия существующего отзыва от пользователя для данного продукта
            existing_review = await db.scalar(
                select(Review).
                where(Review.user_id == get_user.get('id'), Review.product_id == create_review.product_id)
            )
            if existing_review:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already posted a review for this product."
                )
            else:
                await db.execute(insert(Review).values(
                    user_id=get_user.get('id'),
                    product_id=create_review.product_id,
                    comment=create_review.comment,
                    grade=create_review.grade,
                    is_active=True)
                )

                # Обновляем рейтинг продукта
                review_count = await db.scalar(
                    select(func.count(Review.id)).
                    where(Review.product_id == create_review.product_id, Review.is_active == True)
                )
                rating = await db.scalar(select(Product.rating).where(Product.id == create_review.product_id))
                if rating == 0:
                    new_rating = create_review.grade
                elif rating > 0:
                    new_rating = round(((product.rating * review_count + create_review.grade) / (review_count + 1)), 2)

                await db.execute(
                    update(Product).
                    where(Product.id == create_review.product_id).
                    values(rating=new_rating)
                )

                # Сохраняем изменения в базе данных
                await db.commit()
                return {
                    "status_code": status.HTTP_201_CREATED,
                    "transaction": "Review added successfully"
                }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be authenticated to add a review"
        )

# Удаление отзыва. Разрешен доступ только администраторам.
@router.delete("/{review_id}")
async def delete_review(
        db: Annotated[AsyncSession, Depends(get_db)],
        review_id: int,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        review = await db.scalar(select(Review).where(Review.id == review_id, Review.is_active == True))
        if review is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found!"
            )
        else:
            review.is_active = False
            await db.commit()
            return {
                "status_code": status.HTTP_200_OK,
                "transaction": "Review deleted successfully"
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this"
        )