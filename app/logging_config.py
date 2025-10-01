from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from loguru import logger
from uuid import uuid4
import os



# Инициализируем логирование
def configure_logging():
    log_path = os.path.join('/tmp', 'info.log')
    logger.add(
        log_path,
        format="Log: [{extra[log_id]}:{time} - {level} - {message}]",
        level="INFO",
        enqueue=True
    )


# Добавляем функцию логирования в FastAPI
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            if response.status_code in [401, 402, 403, 404]:
                logger.warning(f"Request to {request.url.path} failed")
            else:
                logger.info("Successfully accessed " + request.url.path)
        except Exception as ex:
            logger.error(f"Request to {request.url.path} failed: {ex}")
            response = JSONResponse(content={"success": False}, status_code=500)
        return response

