import os
import sqlite3
import logging
import asyncio
import time
from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import PORT, DOWNLOAD_DIR, PROJECTS_DIR
from app.database import novel_db
from app.api import projects, chapters, outlines, step_summaries, novel, craft, download, ai, settings
from app.api.template import router as template_router
from app.api.generation_template import router as generation_template_router
from app.api.pipeline import router as pipeline_router
from app.api.design import router as design_router
from app.api.structure import router as structure_router
from app.api.execution import router as execution_router

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.environ.get('LOG_DIR', '/app/data'), 'generate.log'), encoding='utf-8'),
    ]
)

app = FastAPI(title="Fanqie Novel API", redirect_slashes=False)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://140.143.210.177,http://140.143.210.177:80").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rate_limit_lock = Lock()
_rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "DELETE"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        with _rate_limit_lock:
            timestamps = _rate_limit_store[client_ip]
            _rate_limit_store[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
            if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"},
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            _rate_limit_store[client_ip].append(now)
    return await call_next(request)


@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        response = await asyncio.wait_for(call_next(request), timeout=580)
        return response
    except asyncio.TimeoutError:
        return JSONResponse({"detail": "请求处理超时"}, status=504)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    if isinstance(exc, HTTPException):
        detail = exc.detail
        status_code = exc.status_code
    else:
        detail = "服务器内部错误，请稍后重试"
        status_code = 500
    headers = {"Access-Control-Allow-Origin": "*"}
    if isinstance(exc, HTTPException) and exc.headers:
        headers.update(exc.headers)
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 验证错误返回 422 (必须在 Exception handler 之后注册)"""
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err["loc"])
        errors.append({"field": field, "message": err["msg"]})
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
        headers={"Access-Control-Allow-Origin": "*"}
    )


app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(outlines.router)
app.include_router(step_summaries.router)
app.include_router(novel.router)
app.include_router(craft.router)
app.include_router(download.router)
app.include_router(ai.router)
app.include_router(settings.router)
app.include_router(template_router)
app.include_router(generation_template_router)
app.include_router(pipeline_router)
app.include_router(design_router)
app.include_router(structure_router)
app.include_router(execution_router)


@app.on_event("startup")
async def startup_event():
    try:
        novel_db.init_db()
    except Exception as e:
        logging.error(f'数据库初始化失败: {e}', exc_info=True)
        raise RuntimeError(f"数据库初始化失败，无法启动服务: {e}") from e
    try:
        from novel_creator.database_v2 import init_db_v2
        init_db_v2()
    except Exception as e:
        logging.error(f'V2数据库初始化失败: {e}', exc_info=True)
    try:
        from app.services.template_service import seed_system_templates
        seed_system_templates()
    except Exception as e:
        logging.warning(f'预置模板初始化失败: {e}')
    try:
        from novel_creator.database import DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE outline_generation_status SET is_running=0, is_paused=0 WHERE is_running=1")
            conn.execute("UPDATE generation_status SET is_running=0, is_paused=0 WHERE is_running=1")
            conn.commit()
        logging.info('已清理陈旧的生成状态')
    except Exception as e:
        logging.error(f'清理陈旧状态失败: {e}', exc_info=True)


if __name__ == "__main__":
    import uvicorn
    print(f'番茄小说服务端 v2 (FastAPI) 已启动: http://0.0.0.0:{PORT}')
    uvicorn.run(app, host="0.0.0.0", port=PORT)
