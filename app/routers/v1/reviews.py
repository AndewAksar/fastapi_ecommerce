from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, insert, select, update
from typing import Annotated, Any

from app.routers.v1.auth import get_current_user
from app.backend.db_depends import get_db
from app.models.reviews import Review
from app.models.products import Product
from app.schemas import CreateReview, MessageResponse, ReviewListResponse, ReviewRead

router = APIRouter(prefix="/reviews", tags=["reviews"])


# Получение полного перечня отзывов. Разрешен доступ всем.
@router.get("/", response_model=ReviewListResponse)
async def all_reviews(
        db: Annotated[AsyncSession, Depends(get_db)],
        limit: int = Query(10, ge=1, le=100, description="Количество отзывов на странице"),
        offset: int = Query(0, ge=0, description="Смещение выборки для пагинации"),
        search: str | None = Query(None, description="Поиск по тексту отзыва"),
        min_price: int | None = Query(None, ge=0, description="Минимальная цена товара"),
        max_price: int | None = Query(None, ge=0, description="Максимальная цена товара"),
):
    """Формируем список отзывов с учётом фильтров и пагинации."""

    # Проверяем корректность диапазона цен до обращения к базе данных.
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price must be less than or equal to max_price",
        )

    review_filters = [Review.is_active == True]

    if search:
        review_filters.append(Review.comment.ilike(f"%{search}%"))

    price_filters: list[Any] = []
    if min_price is not None:
        price_filters.append(Product.price >= min_price)
    if max_price is not None:
        price_filters.append(Product.price <= max_price)

    total_stmt = select(func.count()).select_from(Review).where(*review_filters)
    reviews_stmt = select(Review).where(*review_filters)

    # Для фильтров по цене требуется присоединить таблицу товаров.
    if price_filters:
        total_stmt = total_stmt.join(Product, Review.product_id == Product.id).where(*price_filters)
        reviews_stmt = reviews_stmt.join(Product, Review.product_id == Product.id).where(*price_filters)

    total = await db.scalar(total_stmt)

    reviews_stmt = (
        reviews_stmt
        .order_by(Review.id.desc())
        .limit(limit)
        .offset(offset)
    )
    reviews = await db.scalars(reviews_stmt)

    items = [ReviewRead.model_validate(review) for review in reviews.all()]

    return ReviewListResponse(
        items=items,
        total=total or 0,
        limit=limit,
        offset=offset,
    )

# Получение отзывов по слагу товара. Разрешен доступ всем.
@router.get("/{product_slug}", response_model=ReviewListResponse)
async def products_reviews(
        product_slug: str,
        db: Annotated[AsyncSession, Depends(get_db)],
        limit: int = Query(10, ge=1, le=100, description="Количество отзывов на странице"),
        offset: int = Query(0, ge=0, description="Смещение выборки для пагинации"),
        search: str | None = Query(None, description="Поиск по тексту отзыва"),
        min_price: int | None = Query(None, ge=0, description="Минимальная цена товара"),
        max_price: int | None = Query(None, ge=0, description="Максимальная цена товара"),
):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )

    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price must be less than or equal to max_price",
        )

    # Быстрый выход: если цена товара не удовлетворяет фильтрам, отзывов не будет.
    if min_price is not None and product.price < min_price:
        return ReviewListResponse(items=[], total=0, limit=limit, offset=offset)
    if max_price is not None and product.price > max_price:
        return ReviewListResponse(items=[], total=0, limit=limit, offset=offset)

    review_filters = [Review.is_active == True, Review.product_id == product.id]

    if search:
        review_filters.append(Review.comment.ilike(f"%{search}%"))

    total_stmt = select(func.count()).select_from(Review).where(*review_filters)
    total = await db.scalar(total_stmt)

    reviews_stmt = (
        select(Review)
        .where(*review_filters)
        .order_by(Review.id.desc())
        .limit(limit)
        .offset(offset)
    )
    reviews = await db.scalars(reviews_stmt)

    items = [ReviewRead.model_validate(review) for review in reviews.all()]

    return ReviewListResponse(
        items=items,
        total=total or 0,
        limit=limit,
        offset=offset,
    )

# Добавление отзыва. Разрешен доступ только авторизованным пользователям.
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_review(
        db: Annotated[AsyncSession, Depends(get_db)],
        create_review: CreateReview,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user:
        user_id = get_user['id']
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
                where(Review.user_id == user_id, Review.product_id == create_review.product_id)
            )
            if existing_review:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already posted a review for this product."
                )
            else:
                async with db.begin():
                    review_count = await db.scalar(
                        select(func.count(Review.id)).
                        where(
                            Review.product_id == create_review.product_id,
                            Review.is_active == True,
                        )
                    )
                    review_count = int(review_count or 0)
                    current_rating = float(product.rating or 0)

                    if review_count == 0:
                        current_rating = 0.0

                    new_grade = float(create_review.grade)

                    await db.execute(
                        insert(Review).values(
                            user_id=user_id,
                            product_id=create_review.product_id,
                            comment=create_review.comment,
                            grade=create_review.grade,
                            is_active=True,
                        )
                    )
                    if review_count == 0:
                        new_rating = new_grade
                    else:
                        new_rating = round(
                            (current_rating * review_count + new_grade) / (review_count + 1),
                            2,
                        )
                    await db.execute(
                        update(Product).
                        where(Product.id == create_review.product_id).
                        values(rating=new_rating)
                    )
                return MessageResponse(
                    status_code=status.HTTP_201_CREATED,
                    transaction="Review added successfully"
                )
    else:
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be authenticated to add a review"
        )

# Удаление отзыва. Разрешен доступ только администраторам.
@router.delete("/{review_id}", response_model=MessageResponse)
async def delete_review(
        db: Annotated[AsyncSession, Depends(get_db)],
        review_id: int,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        async with db.begin():
            review = await db.scalar(select(Review).where(Review.id == review_id, Review.is_active == True))
            if review is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found!"
                )

            product_id = review.product_id
            review.is_active = False
            await db.flush()

            review_stats_stmt = (
                select(func.count(Review.id), func.avg(Review.grade))
                .where(Review.product_id == product_id)
                .where(Review.is_active == True)
            )
            review_count, average_grade = (
                await db.execute(review_stats_stmt)
            ).one()

            new_rating = round(float(average_grade), 2) if review_count else 0.0

            await db.execute(
                update(Product)
                .where(Product.id == product_id)
                .values(rating=new_rating)
            )

        return MessageResponse(
            status_code=status.HTTP_200_OK,
            transaction="Review deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this"
        )