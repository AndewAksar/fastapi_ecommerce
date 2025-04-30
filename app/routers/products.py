from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update
from typing import Annotated
from slugify import slugify

from app.schemas import CreateProduct
from app.backend.db_depends import get_db
from app.models import Product, Category

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
async def get_all_products(db: Annotated[Session, Depends(get_db)]):
    products = db.scalars(select(Product).where(Product.is_active == True, Product.stock != 0)).all()
    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
            )
    else:
        return products

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(db: Annotated[Session, Depends(get_db)], create_product: CreateProduct):
    db.execute(insert(Product).values(
        name=create_product.name,
        description=create_product.description,
        price=create_product.price,
        image_url=create_product.image_url,
        stock=create_product.stock,
        category_id=create_product.category,
        slug=slugify(create_product.name),
        is_active=True)
    )
    db.commit()
    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Product has been created successfully!"
    }

@router.get("/{category_slug}")
async def product_by_category(db: Annotated[Session, Depends(get_db)], category_slug: str):
    category = db.scalar(select(Category).where(Category.slug == category_slug, Category.is_active == True))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found!"
        )
    else:
        subcategories = db.scalars(select(Category).where(Category.parent_id == category.id)).all()
        categories_and_subcategories = [category.id] + [i.id for i in subcategories]
        product = db.scalars(
            select(Product).where(
                Product.category_id.in_(categories_and_subcategories),
                Product.is_active == True,
                Product.stock != 0
            )
        ).all()
        return product

@router.get("/detail/{product_slug}")
async def product_detail(db: Annotated[Session, Depends(get_db)], product_slug: str):
    product = db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )
    else:
        return product

@router.put("/{product_slug}")
async def update_product(db: Annotated[Session, Depends(get_db)], product_slug: str, update_product: CreateProduct):
    product = db.scalars(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )
    else:
        db.execute(update(Product).where(Product.slug == product_slug).values(
            name=update_product.name,
            description=update_product.description,
            price=update_product.price,
            image_url=update_product.image_url,
            stock=update_product.stock,
            category_id=update_product.category,
            slug=slugify(update_product.name),
            is_active=True)
        )
    db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Product has been updated successfully!"
    }

@router.delete("/{product_slug}")
async def delete_product(db: Annotated[Session, Depends(get_db)], product_slug: str):
    product = db.scalars(select(Product).where(Product.slug == product_slug, Product.is_active == True))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )
    else:
        db.execute(update(Product).where(Product.slug == product_slug).values(is_active=False))
        db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Product has been deleted successfully!"
        }