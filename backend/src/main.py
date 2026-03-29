"""
DBA Assistant Backend - FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import chat, db, admin, text2sql, monitor, templates, visit


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.core.dependencies import get_container
    from src.config import get_config
    container = get_container()
    container.init(get_config())
    yield


app = FastAPI(title="DBA Assistant API", version="0.1.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(db.router, prefix="/api/db", tags=["database"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(text2sql.router, prefix="/api/db", tags=["text2sql"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["monitor"])
app.include_router(templates.router, prefix="/api", tags=["templates"])
app.include_router(visit.router, prefix="/api", tags=["visit"])


@app.get("/")
async def root():
    return {"message": "DBA Assistant API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
