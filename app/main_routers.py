from fastapi import FastAPI


from app.routers.v1 import auth, category, permission, products, reviews, session
from app.tasks import call_background_task


def setup_routers(app: FastAPI):
    # Создаём подприложение для версии v1
    app_v1 = FastAPI()

    # Запуск асинхронной задачи Celery
    @app_v1.get("/")
    async def hello_world(message: str = None):
        call_background_task.apply_async(args=[message], expires=1000)
        return {'message': f'Hello World! {message}'}

    # Добавляем маршруты к подприложению v1
    app_v1.include_router(category.router)
    app_v1.include_router(products.router)
    app_v1.include_router(auth.router)
    app_v1.include_router(permission.router)
    app_v1.include_router(reviews.router)
    app_v1.include_router(session.router)

    # Монтируем подприложения к основному приложению
    app.mount('/v1', app_v1)

