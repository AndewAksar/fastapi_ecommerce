from fastapi import APIRouter, Request


router = APIRouter(prefix="/sessions", tags=["sessions"])


# Определяем маршруты для работы с сессиями
@router.get("/create_session")
async def session_set(request: Request):
    request.session["my_session"] = "1234"
    return 'ok'

@router.get("/read_session")
async def session_info(request: Request):
    my_var = request.session.get("my_session")
    return my_var

@router.get("/delete_session")
async def session_delete(request: Request):
    my_var = request.session.pop("my_session")
    return my_var