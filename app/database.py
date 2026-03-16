from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb.database = mongodb.client[settings.DATABASE_NAME]
    
    # Создаем индексы
    await mongodb.database.users.create_index("email", unique=True)
    await mongodb.database.achievements.create_index("user_id")
    await mongodb.database.stats.create_index("user_id", unique=True)
    await mongodb.database.history.create_index("user_id")
    
    print("Connected to MongoDB")

async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        print("Closed MongoDB connection")

def get_database():
    return mongodb.database