import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GIGACHAT_CREDENTIALS: str = os.getenv("GIGACHAT_CREDENTIALS", "019cfd98-676c-748d-b95c-bced0f2ed2f9")
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongo:sUKqPJROItGYKHBrszkYkmrlHrAuRFdk@tramway.proxy.rlwy.net:47409")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "achievement_db")
    
    # ✅ Важно! SECRET_KEY должен быть одинаковым для всех инстансов
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Увеличиваем до 60 минут
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()