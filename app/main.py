from fastapi import FastAPI
from app.routers import category, products

app = FastAPI()


@app.get("/")
async def welcome() -> dict:
    return {"message": "Welcome to FastAPI Ecommerce App!"}


app.include_router(category.router)
app.include_router(products.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)