from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import asyncio

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    try:
        print(f"Connecting to MongoDB at: {settings.MONGODB_URL}")
        
        # Добавляем параметры аутентификации
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            # Если нужно указать базу для аутентификации
            authSource="admin"  # или имя вашей базы данных
        )
        
        # Проверяем подключение
        await mongodb.client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        
        mongodb.database = mongodb.client[settings.DATABASE_NAME]
        
        # Создаем индексы с обработкой ошибок
        try:
            await mongodb.database.users.create_index("email", unique=True)
            print("Created users index")
        except Exception as e:
            print(f"Note: users index may already exist: {e}")
        
        try:
            await mongodb.database.achievements.create_index("user_id")
            print("Created achievements index")
        except Exception as e:
            print(f"Note: achievements index may already exist: {e}")
        
        try:
            await mongodb.database.stats.create_index("user_id", unique=True)
            print("Created stats index")
        except Exception as e:
            print(f"Note: stats index may already exist: {e}")
        
        try:
            await mongodb.database.history.create_index("user_id")
            print("Created history index")
        except Exception as e:
            print(f"Note: history index may already exist: {e}")
        
        print("Indexes check completed!")
        
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        print("Closed MongoDB connection")

def get_database():
    return mongodb.database