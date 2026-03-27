"""
DBA Assistant Backend - FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import chat, db, admin, text2sql

app = FastAPI(title="DBA Assistant API", version="0.1.0")

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


@app.get("/")
async def root():
    return {"message": "DBA Assistant API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
