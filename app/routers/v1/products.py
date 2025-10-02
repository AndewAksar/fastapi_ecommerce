from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, insert, or_, select
from typing import Annotated
from slugify import slugify

from app.routers.v1.auth import get_current_user
from app.schemas import CreateProduct, MessageResponse, ProductListResponse, ProductRead
from app.backend.db_depends import get_db
from app.models import Product, Category

router = APIRouter(prefix="/products", tags=["products"])


# Метод получения всех товаров. Разрешен доступ всем.
@router.get("/", response_model=ProductListResponse)
async def get_all_products(
        db: Annotated[AsyncSession, Depends(get_db)],
        limit: int = Query(10, ge=1, le=100, description="Количество элементов на странице"),
        offset: int = Query(0, ge=0, description="Смещение выборки для пагинации"),
        search: str | None = Query(None, description="Поиск по названию и описанию товара"),
        min_price: int | None = Query(None, ge=0, description="Минимальная цена"),
        max_price: int | None = Query(None, ge=0, description="Максимальная цена"),
):
    """Возвращаем список товаров с учётом фильтров и пагинации."""

    # Валидируем диапазон цен, чтобы не строить заведомо пустой запрос к БД.
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price must be less than or equal to max_price",
        )

    filters = [Product.is_active == True, Product.stock > 0]

    # Добавляем условия поиска по тексту, если передан параметр.
    if search:
        search_pattern = f"%{search}%"
        filters.append(or_(
            Product.name.ilike(search_pattern),
            Product.description.ilike(search_pattern)
        ))

    # Ограничения по цене задаются только если пользователь их указал.
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)

    total_stmt = select(func.count()).select_from(Product).where(*filters)
    total = await db.scalar(total_stmt)

    products_stmt = (
        select(Product)
        .where(*filters)
        .order_by(Product.id)
        .limit(limit)
        .offset(offset)
    )
    products = await db.scalars(products_stmt)

    items = [ProductRead.model_validate(product) for product in products.all()]

    return ProductListResponse(
        items=items,
        total=total or 0,
        limit=limit,
        offset=offset,
    )

# Метод создания товара. Разрешен доступ администраторам и продавцам.
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def create_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        create_product: CreateProduct,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin') or get_user['is_supplier']:
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
            return MessageResponse(
                status_code=status.HTTP_201_CREATED,
                transaction="Product has been created successfully!"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have not enough permission to use post-method"
        )

# Метод получения товаров определенной категории. Разрешен доступ всем.
@router.get("/{category_slug}", response_model=ProductListResponse)
async def product_by_category(
        db: Annotated[AsyncSession, Depends(get_db)],
        category_slug: str,
        limit: int = Query(10, ge=1, le=100, description="Количество элементов на странице"),
        offset: int = Query(0, ge=0, description="Смещение выборки для пагинации"),
        search: str | None = Query(None, description="Поиск по названию и описанию товара"),
        min_price: int | None = Query(None, ge=0, description="Минимальная цена"),
        max_price: int | None = Query(None, ge=0, description="Максимальная цена"),
):
    category = await db.scalar(select(Category).where(Category.slug == category_slug, Category.is_active == True))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found!"
        )
    else:
        if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min_price must be less than or equal to max_price",
            )

        subcategories_result = await db.scalars(select(Category).where(Category.parent_id == category.id))
        subcategories = subcategories_result.all()
        categories_and_subcategories = [category.id] + [i.id for i in subcategories]

        filters = [
            Product.category_id.in_(categories_and_subcategories),
            Product.is_active == True,
            Product.stock > 0,
        ]

        # Переиспользуем логику фильтрации по тексту и диапазону цен.
        if search:
            search_pattern = f"%{search}%"
            filters.append(or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            ))
        if min_price is not None:
            filters.append(Product.price >= min_price)
        if max_price is not None:
            filters.append(Product.price <= max_price)

        total_stmt = select(func.count()).select_from(Product).where(*filters)
        total = await db.scalar(total_stmt)

        products_stmt = (
            select(Product)
            .where(*filters)
            .order_by(Product.id)
            .limit(limit)
            .offset(offset)
        )
        products = await db.scalars(products_stmt)

        items = [ProductRead.model_validate(product) for product in products.all()]

        return ProductListResponse(
            items=items,
            total=total or 0,
            limit=limit,
            offset=offset,
        )

# Метод получения детальной информации о товаре. Разрешен доступ всем.
@router.get("/detail/{product_slug}", response_model=ProductRead)
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
        return ProductRead.model_validate(product)

# Метод изменения товара. Разрешен доступ администраторам и продавцам, которые добавили этот товар.
@router.put("/{product_slug}", response_model=MessageResponse)
async def update_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_slug: str,
        update_product: CreateProduct,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        product = await db.scalar(select(Product).where(Product.slug == product_slug))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found!"
            )
        if get_user.get('id') == product.supplier_id or get_user.get('is_admin'):
            category = await db.scalar(select(Category).where(Category.id == update_product.category))
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found!"
                )
            else:
                product.name = update_product.name
                product.description = update_product.description
                product.price = update_product.price
                product.image_url = update_product.image_url
                product.stock = update_product.stock
                product.category_id = update_product.category
                product.slug = slugify(update_product.name)
                product.is_active = True

                await db.commit()
                return MessageResponse(
                    status_code=status.HTTP_200_OK,
                    transaction="Product has been updated successfully!"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not admin or supplier of this product!"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have not enough permission to use update-method"
        )

# Метод удаления товара. Разрешен доступ администраторам и продавцам, которые добавили этот товар.
@router.delete("/{product_slug}", response_model=MessageResponse)
async def delete_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_slug: str,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        product = await db.scalar(select(Product).where(Product.slug == product_slug, Product.is_active == True))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found!"
            )
        if get_user.get('id') == product.supplier_id or get_user.get('is_admin'):
            product.is_active = False
            await db.commit()
            return MessageResponse(
                status_code=status.HTTP_200_OK,
                transaction="Product has been deleted successfully!"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not admin or supplier of this product!"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have not enough permission to use delete-method"
        )