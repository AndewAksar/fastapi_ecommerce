from fastapi import FastAPI
from app.routers.v1 import auth, category, permission, products, reviews

# Создаём основное приложение
app = FastAPI(
    title="FastAPI Ecommerce App",
    version="1.0.0",
    description="Ecommerce API with versioning",
    servers=[
        {"url": "/v1", "description": "Version 1"}
    ]
)

# Создаём подприложение для версии v1
app_v1 = FastAPI()


# Определяем маршрут приветствия для основного приложения
@app.get("/")
async def welcome() -> dict:
    return {"message": "Welcome to FastAPI Ecommerce App!"}

# Добавляем маршруты к подприложению v1
app_v1.include_router(category.router, prefix="/v1")
app_v1.include_router(products.router, prefix="/v1")
app_v1.include_router(auth.router, prefix="/v1")
app_v1.include_router(permission.router, prefix="/v1")
app_v1.include_router(reviews.router, prefix="/v1")

# Монтируем подприложения к основному приложению
app.mount('/v1', app_v1)


# Запуск приложения (если запускаем как скрипт)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)