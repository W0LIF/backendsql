from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import asyncio

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    try:
        print(f"🔌 Connecting to MongoDB at: {settings.MONGODB_URL}")
        
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Проверяем подключение
        await mongodb.client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        mongodb.database = mongodb.client[settings.DATABASE_NAME]
        
        # Создаем индексы
        try:
            await mongodb.database.users.create_index("email", unique=True)
            print("✅ Created users index")
        except Exception as e:
            print(f"⚠️ Users index: {e}")
        
        try:
            await mongodb.database.achievements.create_index("user_id")
            print("✅ Created achievements index")
        except Exception as e:
            print(f"⚠️ Achievements index: {e}")
        
        try:
            await mongodb.database.stats.create_index("user_id", unique=True)
            print("✅ Created stats index")
        except Exception as e:
            print(f"⚠️ Stats index: {e}")
        
        try:
            await mongodb.database.history.create_index("user_id")
            await mongodb.database.history.create_index("created_at")
            print("✅ Created history indexes")
        except Exception as e:
            print(f"⚠️ History indexes: {e}")
        
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        print("✅ Closed MongoDB connection")

def get_database():
    return mongodb.database