import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Берем URL из переменной окружения, которую Railway создаст автоматически
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongo:sUKqPJROItGYKHBrszkYkmrlHrAuRFdk@tramway.proxy.rlwy.net:47409")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "achievement_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()