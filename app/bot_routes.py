import os
import json
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_community.chat_models import GigaChat

from .schemas import BotQueryRequest, BotQueryResponse, HistoryResponse
from .auth_routes import get_current_user
from .database import get_database
from .achievement_routes import check_and_unlock_achievements

router = APIRouter(prefix="/bot", tags=["bot"])

# LANGCHAIN 

def load_all_city_docs():
    """Загружает данные из всех папок внутри ./data/"""
    base_path = "./data"
    documents = []
    
    if os.path.exists(base_path):
        # Проходим по всем подпапкам (piter, moscow, samara)
        for city_folder in os.listdir(base_path):
            city_path = os.path.join(base_path, city_folder)
            if os.path.isdir(city_path):
                for file in os.listdir(city_path):
                    if file.endswith(".json"):
                        try:
                            with open(os.path.join(city_path, file), 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                text = f"{data.get('title', '')} {data.get('content', '')}"
                                # Добавляем город в метаданные, чтобы ИИ знал, откуда инфа
                                documents.append(Document(page_content=text, metadata={"city": city_folder}))
                        except Exception:
                            continue
    return documents

# Инициализация (сработает один раз при запуске сервера)
all_docs = load_all_city_docs()
retriever = BM25Retriever.from_documents(all_docs) if all_docs else None

# ключ
llm = GigaChat(credentials="MDE5Y2ZkOTgtNjc2Yy03NDhkLWI5NWMtYmNlZDBmMmVkMmY5OjFjZDY4ZWNhLWQzZmEtNDFkMS04NjMxLTM2OGI5NDg4ZGQzOA==", 
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS")

async def get_ai_response(query: str) -> str:
    """Функция поиска по всем городам и генерации ответа ИИ"""
    if not retriever:
        return "Извините, база данных городов временно недоступна."
    
    try:
        # Ищем 5 самых подходящих кусков текста по всем городам
        search_results = retriever.get_relevant_documents(query)
        context = "\n\n".join([f"[{doc.metadata['city']}]: {doc.page_content}" for doc in search_results[:5]])
        
        prompt = (
            f"Ты — умный городской ассистент по России. Твоя задача — отвечать на вопросы пользователей, "
            f"используя предоставленные данные по городам (Санкт-Петербург, Москва, Самара).\n\n"
            f"ДАННЫЕ ИЗ БАЗЫ:\n{context}\n\n"
            f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {query}\n\n"
            f"ОТВЕТ (будь вежлив и конкретен):"
        )
        
        res = llm.invoke(prompt)
        return res.content
    except Exception as e:
        return f"Ошибка: {str(e)}. Запрос: {query}"
    
@router.post("/query", response_model=BotQueryResponse)
async def bot_query(request: BotQueryRequest):
# async def bot_query(
#     request: BotQueryRequest,
#     current_user: dict = Depends(get_current_user)
# ):
    db = get_database()
    # user_id = str(current_user["_id"])
    user_id = "69b9dc7f7a4b6d2eff43d4ba"
    
    # замена заглушки на ии
    response_text = await get_ai_response(request.query)
    
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
            streak_days = stats["streak_days"] + 1
        elif last_query and last_query.date() == today:
            streak_days = stats["streak_days"]
        else:
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
    
    new_achievements = await check_and_unlock_achievements(user_id, stats["query_count"])
    achievements_count = await db.achievements.count_documents({"user_id": user_id, "is_unlocked": True})
    
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

# Тест

@router.post("/test-query") # Новый путь специально для теста
async def test_bot_query(request: BotQueryRequest):
    # Твоя логика поиска и ИИ
    response_text = await get_ai_response(request.query)
    return {"status": "success", "response": response_text}