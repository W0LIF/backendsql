from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import connect_to_mongo, close_mongo_connection
from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .achievement_routes import router as achievement_router
from .bot_routes import router as bot_router

# Создаем директории для статических файлов
os.makedirs("uploads/avatars", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan, title="Achievement Bot API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Роуты
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(achievement_router)
app.include_router(bot_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Achievement Bot API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}