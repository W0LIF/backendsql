import os
import json
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_community.chat_models import GigaChat

# ✅ Импортируем из schemas
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
        for city_folder in os.listdir(base_path):
            city_path = os.path.join(base_path, city_folder)
            if os.path.isdir(city_path):
                for file in os.listdir(city_path):
                    if file.endswith(".json"):
                        try:
                            with open(os.path.join(city_path, file), 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                                title = data.get('title', '')
                                body = data.get('main_content') or data.get('content') or data.get('description') or ''
                                text = f"{title} {body}"
                                
                                documents.append(Document(page_content=text, metadata={"city": city_folder}))
                        except Exception as e:
                            print(f"Ошибка в файле {file}: {e}")
                            continue
    return documents

all_docs = load_all_city_docs()
retriever = BM25Retriever.from_documents(all_docs) if all_docs else None

llm = GigaChat(
    credentials="MDE5ZDAxYWYtYjRiNS03NjkyLWE0YWUtMzUyOTc4MzNmMzNjOmU4MzIyNGI5LTk2MDItNDNkZC04NzQwLTg2YmYyNDI4OGQ4Mg==", 
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS"
)

async def get_ai_response(query: str, city: str) -> str:
    if not retriever:
        return "Извините, база данных городов временно недоступна."
    
    try:
        all_relevant = retriever.get_relevant_documents(query, k=20)

        search_results = [
            doc for doc in all_relevant 
            if doc.metadata.get("city") == city
        ][:5]
        
        if not search_results:
            return f"К сожалению, у меня пока нет информации по вашему запросу в городе {city}."

        context = "\n\n".join([
            f"Источник ({doc.metadata.get('site', 'сайт')}): {doc.page_content}" 
            for doc in search_results[:5]
        ])
        
        prompt = (
            f"Ты — официальный цифровой помощник по городам России. Твоя специализация сейчас: {city}.\n"
            f"ИНСТРУКЦИЯ:\n"
            f"1. Используй ТОЛЬКО предоставленный контекст ниже для ответа.\n"
            f"2. Если в данных нет ответа, вежливо скажи, что пока не владеешь этой информацией по городу {city}.\n"
            f"3. Пиши кратко, вежливо, структурировано (используй списки) и дружелюбно.\n"
            f"4. Ссылайся на конкретные адреса или сайты, если они есть в тексте.\n"
            f"5. Если пользователь спрашивает 'куда сходить', 'что посмотреть' или 'где погулять' в {city}, "
            f"обязательно предлагай варианты из секций: выставки, экскурсии, события, музеи и парки, фестивали, развлечения, афиши, выступления."
            f"которые есть в данных ниже.\n"
            f"6. Если пользователь спрашивает, как оформить документ, ищи МФЦ.\n"
            f"7. В ответе ЗАПРЕЩЕНО использовать символы звездочек для выделения текста. \n"
            f"ДАННЫЕ ИЗ БАЗЫ:\n{context}\n\n"
            f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {query}\n\n"
            f"ТВОЙ ОТВЕТ:"
        )
        
        res = llm.invoke(prompt)
        return res.content

    except Exception as e:
        return f"Ошибка: {str(e)}"
    
@router.post("/query", response_model=BotQueryResponse)
async def bot_query(
    request: BotQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = str(current_user["_id"])
    
    print(f"📨 Bot query from user {user_id}: {request.query}, city: {request.city}")
    
    response_text = await get_ai_response(request.query, request.city)
    
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

@router.post("/test-query")
async def test_bot_query(request: BotQueryRequest):
    response_text = await get_ai_response(request.query, request.city)
    return {"status": "success", "response": response_text}