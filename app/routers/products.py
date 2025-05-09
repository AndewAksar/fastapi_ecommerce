from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
from typing import Annotated
from slugify import slugify

from app.routers.auth import get_current_user
from app.schemas import CreateProduct
from app.backend.db_depends import get_db
from app.models import Product, Category

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
async def get_all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where(Product.is_active == True, Product.stock > 0))
    all_products = products.all()
    if all_products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
            )
    else:
        return all_products

# Метод создания товара. Разрешен доступ администраторам и продавцам.
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        create_product: CreateProduct,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('admin') or get_user.get('supplier'):
        category = await db.scalar(select(Category).where(Category.id == create_product.category))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found!"
            )
        else:
            await db.execute(insert(Product).values(
                name=create_product.name,
                description=create_product.description,
                price=create_product.price,
                image_url=create_product.image_url,
                stock=create_product.stock,
                category_id=create_product.category,
                supplier_id=get_user.get('id'),
                slug=slugify(create_product.name),
                is_active=True)
            )
            await db.commit()
            return {
                "status_code": status.HTTP_201_CREATED,
                "transaction": "Product has been created successfully!"
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method"
        )

@router.get("/{category_slug}")
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug, Category.is_active == True))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found!"
        )
    else:
        subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id)).all()
        categories_and_subcategories = [category.id] + [i.id for i in subcategories]
        product = await db.scalars(
            select(Product).where(
                Product.category_id.in_(categories_and_subcategories),
                Product.is_active == True,
                Product.stock > 0
            )
        )
        return product.all()

@router.get("/detail/{product_slug}")
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(
        select(Product).where(
            Product.slug == product_slug,
            Product.is_active == True,
            Product.stock > 0
        )
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )
    else:
        return product

@router.put("/{product_slug}")
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str, update_product: CreateProduct):
    product = await db.scalars(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )
    category = await db.scalar(select(Category).where(Category.id == update_product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found!"
        )
    else:
        product.name = update_product.name,
        product.description = update_product.description,
        product.price = update_product.price,
        product.image_url = update_product.image_url,
        product.stock = update_product.stock,
        product.category_id = update_product.category,
        product.slug = slugify(update_product.name),
        product.is_active = True

        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Product has been updated successfully!"
        }

@router.delete("/{product_slug}")
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalars(select(Product).where(Product.slug == product_slug, Product.is_active == True))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found!"
        )
    else:
        product.is_active = False
        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Product has been deleted successfully!"
        }