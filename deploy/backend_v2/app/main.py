import os
import sys
import sqlite3
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import PORT, DOWNLOAD_DIR, PROJECTS_DIR
from app.database import novel_db
from app.api import projects, chapters, outlines, step_summaries, novel, craft, download, ai
from app.api.pipeline import router as pipeline_router
from app.api.design import router as design_router
from app.api.structure import router as structure_router
from app.api.execution import router as execution_router

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(os.environ.get('LOG_DIR', '/app/data'), 'generate.log'),
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    encoding='utf-8'
)

app = FastAPI(title="Fanqie Novel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误"},
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
app.include_router(pipeline_router)
app.include_router(design_router)
app.include_router(structure_router)
app.include_router(execution_router)


@app.on_event("startup")
async def startup_event():
    novel_db.init_db()
    try:
        from novel_creator.database_v2 import init_db_v2
        init_db_v2()
    except Exception as e:
        print(f'V2数据库初始化失败: {e}')
    try:
        from novel_creator.database import DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE outline_generation_status SET is_running=0, is_paused=0 WHERE is_running=1")
            conn.execute("UPDATE generation_status SET is_running=0, is_paused=0 WHERE is_running=1")
            conn.commit()
        print('已清理陈旧的生成状态')
    except Exception as e:
        print(f'清理陈旧状态失败: {e}')


if __name__ == "__main__":
    import uvicorn
    print(f'番茄小说服务端 v2 (FastAPI) 已启动: http://0.0.0.0:{PORT}')
    uvicorn.run(app, host="0.0.0.0", port=PORT)
