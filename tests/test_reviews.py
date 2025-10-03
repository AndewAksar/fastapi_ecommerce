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
        user_3 = User(
            first_name="Mike",
            last_name="Smith",
            username="mikesmith",
            email="mike@example.com",
            hashed_password="hashed",
        )
        user_4 = User(
            first_name="Kate",
            last_name="Smith",
            username="katesmith",
            email="kate@example.com",
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
        db_session.add_all([category, user_1, user_2, user_3, user_4, product])
        await db_session.flush()
        first_review = Review(
            user_id=user_1.id,
            product_id=product.id,
            comment="Initial review",
            grade=5,
            is_active=True,
        )
        second_review = Review(
            user_id=user_2.id,
            product_id=product.id,
            comment="Second review",
            grade=4,
            is_active=True,
        )
        product.rating = 4.5
        db_session.add_all([first_review, second_review])


    new_review = CreateReview(product_id=product.id, comment="Great!", grade=5)
    response = await add_review(db_session, new_review, {"id": user_3.id})
    assert response.status_code == 201


    rating_after_third = await db_session.scalar(
        select(Product.rating).where(Product.id == product.id)
    )
    assert rating_after_third == pytest.approx(4.67, abs=1e-2)


    fourth_review = CreateReview(product_id=product.id, comment="Not bad", grade=3)
    response_second = await add_review(db_session, fourth_review, {"id": user_4.id})
    assert response_second.status_code == 201


    rating_after_fourth = await db_session.scalar(
        select(Product.rating).where(Product.id == product.id)
    )
    assert rating_after_fourth == pytest.approx(4.25, abs=1e-2)


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