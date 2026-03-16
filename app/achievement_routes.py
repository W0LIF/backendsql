from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from typing import List

from .models import AchievementResponse, StatsResponse
from .auth_routes import get_current_user
from .database import get_database

router = APIRouter(prefix="/user", tags=["achievements"])

@router.get("/achievements", response_model=dict)
async def get_achievements(current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    achievements = await db.achievements.find(
        {"user_id": str(current_user["_id"])}
    ).to_list(None)
    
    return {
        "achievements": [
            AchievementResponse(
                id=str(a["_id"]),
                title=a["title"],
                description=a["description"],
                icon=a["icon"],
                unlocked_at=a.get("unlocked_at"),
                is_unlocked=a.get("is_unlocked", False)
            ) for a in achievements
        ]
    }

@router.get("/stats", response_model=dict)
async def get_stats(current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    stats = await db.stats.find_one({"user_id": str(current_user["_id"])})
    
    if not stats:
        stats = {
            "query_count": 0,
            "streak_days": 0,
            "total_days": 0,
            "achievements_count": 0
        }
    
    # Обновляем streak_days если нужно
    if stats.get("last_query_date"):
        last_query = stats["last_query_date"]
        today = datetime.utcnow().date()
        
        if last_query.date() == today - timedelta(days=1):
            # Было вчера, увеличиваем streak
            stats["streak_days"] += 1
        elif last_query.date() < today - timedelta(days=1):
            # Было раньше, сбрасываем streak
            stats["streak_days"] = 1
        
        await db.stats.update_one(
            {"user_id": str(current_user["_id"])},
            {"$set": {"streak_days": stats["streak_days"]}}
        )
    
    return stats

async def check_and_unlock_achievements(user_id: str, query_count: int):
    db = get_database()
    new_achievements = []
    
    # Проверяем достижения
    achievements_to_check = [
        {"title": "Первый запрос", "condition": query_count >= 1},
        {"title": "Активный пользователь", "condition": query_count >= 10},
        {"title": "Эксперт", "condition": query_count >= 50},
        {"title": "Мастер", "condition": query_count >= 100},
        {"title": "Легенда", "condition": query_count >= 500},
    ]
    
    for ach in achievements_to_check:
        if ach["condition"]:
            achievement = await db.achievements.find_one({
                "user_id": user_id,
                "title": ach["title"]
            })
            
            if achievement and not achievement.get("is_unlocked"):
                # Разблокируем достижение
                await db.achievements.update_one(
                    {"_id": achievement["_id"]},
                    {
                        "$set": {
                            "is_unlocked": True,
                            "unlocked_at": datetime.utcnow()
                        }
                    }
                )
                
                achievement["is_unlocked"] = True
                achievement["unlocked_at"] = datetime.utcnow()
                new_achievements.append(achievement)
    
    return new_achievements