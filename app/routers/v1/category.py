from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from typing import Annotated
from slugify import slugify

from app.routers.v1.auth import get_current_user
from app.backend.db_depends import get_db
from app.schemas import CategoryRead, CreateCategory, MessageResponse
from app.models import Category

router = APIRouter(prefix="/category", tags=["category"])


# Получение всех категорий.
@router.get("/", response_model=list[CategoryRead])
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    categories = await db.scalars(select(Category).where(Category.is_active == True))
    all_categories = categories.all()
    return [CategoryRead.model_validate(category) for category in all_categories]

# Создание категории. Разрешено только для админа.
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        db: Annotated[AsyncSession, Depends(get_db)],
        create_category: CreateCategory,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        await db.execute(insert(Category).values(
            name=create_category.name,
            parent_id=create_category.parent_id,
            slug=slugify(create_category.name))
        )
        await db.commit()
        return MessageResponse(
            status_code=status.HTTP_201_CREATED,
            transaction="Success"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this"
        )

@router.put("/{category_slug}", response_model=MessageResponse)
async def put_category(
        db: Annotated[AsyncSession, Depends(get_db)],
        category_slug: str,
        update_category: CreateCategory,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        category = await db.scalar(select(Category).where(Category.slug == category_slug))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category is no found"
            )
        else:
            category.name = update_category.name
            category.parent_id = update_category.parent_id
            category.slug = slugify(update_category.name)
        
            await db.commit()
            return MessageResponse(
                status_code=status.HTTP_200_OK,
                transaction="Category update is successful"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this"
        )

@router.delete("/{category_slug}", response_model=MessageResponse)
async def delete_category(
        db: Annotated[AsyncSession, Depends(get_db)],
        category_slug: str,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        category = await db.scalar(select(Category).where(Category.slug == category_slug, Category.is_active == True))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        else:
            category.is_active = False
            await db.commit()
            return MessageResponse(
                status_code=status.HTTP_200_OK,
                transaction="Category delete is successful"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this"
        )