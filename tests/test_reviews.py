import pytest
from sqlalchemy import select

from app.models.category import Category
from app.models.products import Product
from app.models.reviews import Review
from app.models.user import User
from app.routers.v1.reviews import add_review, delete_review
from app.schemas import CreateReview


@pytest.mark.asyncio
async def test_add_review_updates_rating(db_session):
    async with db_session.begin():
        category = Category(name="Electronics", slug="electronics")
        user_1 = User(
            first_name="John",
            last_name="Doe",
            username="johndoe",
            email="john@example.com",
            hashed_password="hashed",
        )
        user_2 = User(
            first_name="Jane",
            last_name="Doe",
            username="janedoe",
            email="jane@example.com",
            hashed_password="hashed",
        )
        product = Product(
            name="Smartphone",
            slug="smartphone",
            description="Test product",
            price=100,
            image_url="http://example.com/img.jpg",
            stock=5,
            category=category,
        )
        db_session.add_all([category, user_1, user_2, product])

    review_payload = CreateReview(product_id=product.id, comment="Great!", grade=5)
    response = await add_review(db_session, review_payload, {"id": user_1.id})
    assert response["status_code"] == 201

    product_rating = await db_session.scalar(select(Product.rating).where(Product.id == product.id))
    assert product_rating == pytest.approx(5.0)

    second_review = CreateReview(product_id=product.id, comment="Not bad", grade=3)
    await add_review(db_session, second_review, {"id": user_2.id})

    updated_rating = await db_session.scalar(select(Product.rating).where(Product.id == product.id))
    assert updated_rating == pytest.approx(4.0)


@pytest.mark.asyncio
async def test_delete_review_updates_rating_and_handles_empty_state(db_session):
    async with db_session.begin():
        category = Category(name="Books", slug="books")
        user_1 = User(
            first_name="Alice",
            last_name="Smith",
            username="alicesmith",
            email="alice@example.com",
            hashed_password="hashed",
        )
        user_2 = User(
            first_name="Bob",
            last_name="Smith",
            username="bobsmith",
            email="bob@example.com",
            hashed_password="hashed",
        )
        product = Product(
            name="Novel",
            slug="novel",
            description="Interesting book",
            price=20,
            image_url="http://example.com/book.jpg",
            stock=10,
            category=category,
        )
        db_session.add_all([category, user_1, user_2, product])

    await add_review(db_session, CreateReview(product_id=product.id, comment="Nice", grade=4), {"id": user_1.id})
    await add_review(db_session, CreateReview(product_id=product.id, comment="Ok", grade=2), {"id": user_2.id})

    reviews = await db_session.scalars(
        select(Review).where(Review.product_id == product.id).order_by(Review.id)
    )
    review_list = reviews.all()
    assert len(review_list) == 2

    await delete_review(db_session, review_list[0].id, {"is_admin": True})
    rating_after_first_delete = await db_session.scalar(
        select(Product.rating).where(Product.id == product.id)
    )
    assert rating_after_first_delete == pytest.approx(2.0)

    await delete_review(db_session, review_list[1].id, {"is_admin": True})
    rating_after_second_delete = await db_session.scalar(
        select(Product.rating).where(Product.id == product.id)
    )
    assert rating_after_second_delete == pytest.approx(0.0)

    remaining_reviews = await db_session.scalars(
        select(Review).where(Review.product_id == product.id, Review.is_active == True)
    )
    assert remaining_reviews.all() == []