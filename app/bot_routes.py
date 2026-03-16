from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List

from .models import BotQueryRequest, BotQueryResponse, HistoryResponse
from .auth_routes import get_current_user
from .database import get_database
from .achievement_routes import check_and_unlock_achievements

router = APIRouter(prefix="/bot", tags=["bot"])

# Простой ответ бота (в реальном проекте здесь может быть интеграция с AI)
def get_bot_response(query: str) -> str:
    responses = {
        "привет": "Здравствуйте! Чем могу помочь?",
        "как дела": "У меня всё отлично, спасибо!",
        "пока": "До свидания! Обращайтесь ещё!",
    }
    
    # Поиск по ключевым словам
    query_lower = query.lower()
    for key, response in responses.items():
        if key in query_lower:
            return response
    
    return f"Я получил ваш запрос: '{query}'. В разработке находится более интеллектуальный ответ."

@router.post("/query", response_model=BotQueryResponse)
async def bot_query(
    request: BotQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = str(current_user["_id"])
    
    # Получаем ответ бота
    response_text = get_bot_response(request.query)
    
    # Сохраняем в историю
    history_entry = {
        "user_id": user_id,
        "query": request.query,
        "response": response_text,
        "created_at": datetime.utcnow()
    }
    await db.history.insert_one(history_entry)
    
    # Обновляем статистику
    stats = await db.stats.find_one({"user_id": user_id})
    if not stats:
        stats = {
            "user_id": user_id,
            "query_count": 0,
            "streak_days": 1,
            "total_days": 1,
            "achievements_count": 0,
            "last_query_date": datetime.utcnow()
        }
        await db.stats.insert_one(stats)
    else:
        new_query_count = stats["query_count"] + 1
        today = datetime.utcnow().date()
        last_query = stats.get("last_query_date")
        
        if last_query and last_query.date() == today - timedelta(days=1):
            # Продолжаем стрик
            streak_days = stats["streak_days"] + 1
        elif last_query and last_query.date() == today:
            # Уже сегодня был запрос
            streak_days = stats["streak_days"]
        else:
            # Сбрасываем стрик
            streak_days = 1
        
        await db.stats.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "query_count": new_query_count,
                    "streak_days": streak_days,
                    "last_query_date": datetime.utcnow()
                }
            }
        )
        
        stats["query_count"] = new_query_count
        stats["streak_days"] = streak_days
    
    # Проверяем и разблокируем достижения
    new_achievements = await check_and_unlock_achievements(user_id, stats["query_count"])
    
    # Получаем общее количество достижений
    achievements_count = await db.achievements.count_documents({
        "user_id": user_id,
        "is_unlocked": True
    })
    
    # Обновляем количество достижений в статистике
    await db.stats.update_one(
        {"user_id": user_id},
        {"$set": {"achievements_count": achievements_count}}
    )
    
    return BotQueryResponse(
        response=response_text,
        query_count=stats["query_count"],
        new_achievements=[
            {
                "id": str(a["_id"]),
                "title": a["title"],
                "description": a["description"],
                "icon": a["icon"],
                "unlocked_at": a.get("unlocked_at"),
                "is_unlocked": True
            } for a in new_achievements
        ]
    )

@router.get("/history", response_model=dict)
async def get_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    db = get_database()
    
    history = await db.history.find(
        {"user_id": str(current_user["_id"])}
    ).sort("created_at", -1).limit(limit).to_list(None)
    
    return {
        "history": [
            {
                "query": h["query"],
                "response": h["response"],
                "created_at": h["created_at"].isoformat()
            } for h in history
        ]
    }