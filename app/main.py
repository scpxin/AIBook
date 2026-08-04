import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api_keys import router as api_keys_router
from app.api.design import router as design_router
from app.api.download import router as download_router
from app.api.execution import router as execution_router
from app.api.generation_template import router as generation_template_router
from app.api.pipeline import router as pipeline_router
from app.api.projects import router as projects_router
from app.api.settings import router as settings_router
from app.api.structure import router as structure_router
from app.api.template import router as template_router
from app.config import ALLOWED_ORIGINS, DOWNLOAD_DIR, PORT, PROJECTS_DIR
from app.database import novel_db


class JsonFormatter(logging.Formatter):
    """JSON 结构化日志格式"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        return json.dumps(log_data, ensure_ascii=False)


os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(os.environ.get('LOG_DIR', '/app/data'), exist_ok=True)

log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
json_log_handler = os.environ.get('JSON_LOG', 'false').lower() == 'true'

if json_log_handler:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
else:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))

file_handler = logging.FileHandler(
    os.path.join(os.environ.get('LOG_DIR', '/app/data'), 'generate.log'),
    encoding='utf-8'
)
if json_log_handler:
    file_handler.setFormatter(JsonFormatter())
else:
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))

logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    handlers=[handler, file_handler],
)

app = FastAPI(title="Fanqie Novel API", redirect_slashes=False)

ALLOWED_ORIGINS = ALLOWED_ORIGINS or ["*"]

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
_RATE_LIMIT_SWEEP_THRESHOLD = 10000
_RATE_LIMITED_GET_PREFIXES = (
    "/api/download/start",
    "/api/download/pause",
    "/api/download/resume",
    "/api/download/saved",
    "/api/downloads/content",
)


def _client_ip(request: Request) -> str:
    """获取真实客户端 IP (优先 X-Forwarded-For, 兼容 nginx 反代)"""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    is_write = request.method in ("POST", "PUT", "DELETE")
    is_mutating_get = (
        request.method == "GET"
        and request.url.path.startswith(_RATE_LIMITED_GET_PREFIXES)
    )
    if is_write or is_mutating_get:
        client_ip = _client_ip(request)
        now = time.time()
        with _rate_limit_lock:
            timestamps = _rate_limit_store[client_ip]
            _rate_limit_store[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
            if not _rate_limit_store[client_ip]:
                del _rate_limit_store[client_ip]
            elif len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"},
                    headers={"Access-Control-Allow-Origin": ALLOWED_ORIGINS[0] if len(ALLOWED_ORIGINS) == 1 else "*"}
                )
            _rate_limit_store[client_ip].append(now)
            if len(_rate_limit_store) > _RATE_LIMIT_SWEEP_THRESHOLD:
                for ip in list(_rate_limit_store):
                    expired = [t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
                    if expired:
                        _rate_limit_store[ip] = expired
                    else:
                        del _rate_limit_store[ip]
    return await call_next(request)


@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        response = await asyncio.wait_for(call_next(request), timeout=580)
        return response
    except TimeoutError:
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
    headers = {"Access-Control-Allow-Origin": ALLOWED_ORIGINS[0] if len(ALLOWED_ORIGINS) == 1 else "*"}
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
        headers={"Access-Control-Allow-Origin": ALLOWED_ORIGINS[0] if len(ALLOWED_ORIGINS) == 1 else "*"}
    )


app.include_router(api_keys_router)
app.include_router(projects_router)
app.include_router(download_router)
app.include_router(settings_router)
app.include_router(template_router)
app.include_router(generation_template_router)
app.include_router(pipeline_router)
app.include_router(design_router)
app.include_router(structure_router)
app.include_router(execution_router)

# Metrics 数据
_metrics = {
    'requests_total': 0,
    'requests_by_method': defaultdict(int),
    'requests_by_status': defaultdict(int),
    'response_time_sum_ms': 0.0,
    'errors_total': 0,
    'start_time': time.time(),
}
_metrics_lock = Lock()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """记录请求指标 (排除 /metrics 自身避免自计数)"""
    if request.url.path == "/metrics":
        return await call_next(request)

    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    with _metrics_lock:
        _metrics['requests_total'] += 1
        _metrics['requests_by_method'][request.method] += 1
        _metrics['requests_by_status'][response.status_code] += 1
        _metrics['response_time_sum_ms'] += duration_ms
        if response.status_code >= 400:
            _metrics['errors_total'] += 1

    return response


@app.get("/metrics")
async def get_metrics():
    """Prometheus 格式指标"""
    uptime = time.time() - _metrics['start_time']
    avg_response_time = (
        _metrics['response_time_sum_ms'] / _metrics['requests_total']
        if _metrics['requests_total'] > 0 else 0.0
    )

    lines = [
        '# HELP app_uptime_seconds Application uptime in seconds',
        '# TYPE app_uptime_seconds counter',
        f'app_uptime_seconds {uptime:.2f}',
        '# HELP app_requests_total Total number of requests',
        '# TYPE app_requests_total counter',
        f'app_requests_total {_metrics["requests_total"]}',
        '# HELP app_response_time_avg_ms Average response time in milliseconds',
        '# TYPE app_response_time_avg_ms gauge',
        f'app_response_time_avg_ms {avg_response_time:.2f}',
        '# HELP app_errors_total Total number of errors',
        '# TYPE app_errors_total counter',
        f'app_errors_total {_metrics["errors_total"]}',
    ]

    for method, count in _metrics['requests_by_method'].items():
        lines.append(f'app_requests_by_method{{method="{method}"}} {count}')

    for status, count in _metrics['requests_by_status'].items():
        lines.append(f'app_requests_by_status{{status="{status}"}} {count}')

    return '\n'.join(lines), 200, {'Content-Type': 'text/plain'}


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
        logging.error(f'V2数据库初始化失败，服务将在无V2数据库模式下运行: {e}', exc_info=True)
    try:
        from app.services.template_service import seed_system_templates
        seed_system_templates()
    except Exception as e:
        logging.warning(f'预置模板初始化失败: {e}')


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from novel_creator.data_bridge import DataBridge
        DataBridge.close()
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    logging.info(f'番茄小说服务端 v2 (FastAPI) 已启动: http://0.0.0.0:{PORT}')
    uvicorn.run(app, host="0.0.0.0", port=PORT)
