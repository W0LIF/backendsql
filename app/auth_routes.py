from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
import random
import string
from bson import ObjectId

from .models import (
    UserCreate, UserLogin, TokenResponse, UserResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from .database import get_database
from .config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Хранилище кодов для сброса пароля
reset_codes = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        print(f"🔍 Looking for user with ID: {user_id}")
        
        if user_id is None:
            print("❌ No user_id in token")
            raise credentials_exception
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise credentials_exception
    
    db = get_database()
    try:
        # Ищем пользователя по ObjectId
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            print(f"❌ User not found with ID: {user_id}")
            raise credentials_exception
        
        print(f"✅ User found: {user['email']}")
        return user
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        raise credentials_exception

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user_data: UserCreate):
    db = get_database()
    
    # Проверяем существующего пользователя
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Создаем пользователя
    user_dict = user_data.dict(exclude={"password"})
    user_dict["hashed_password"] = get_password_hash(user_data.password)
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    result = await db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)
    user_dict["_id"] = result.inserted_id
    
    print(f"✅ User registered with ID: {user_id}")
    
    # Создаем статистику для пользователя
    await db.stats.insert_one({
        "user_id": user_id,
        "query_count": 0,
        "streak_days": 0,
        "total_days": 0,
        "achievements_count": 0,
        "last_query_date": None
    })
    
    # Создаем начальные достижения
    initial_achievements = [
        {"user_id": user_id, "title": "Новичок", 
         "description": "Зарегистрироваться в приложении", "icon": "🎉", "is_unlocked": True, "unlocked_at": datetime.utcnow()},
        {"user_id": user_id, "title": "Первый запрос", 
         "description": "Отправить первый запрос боту", "icon": "🤖", "is_unlocked": False},
        {"user_id": user_id, "title": "Активный пользователь", 
         "description": "Отправить 10 запросов", "icon": "🔥", "is_unlocked": False},
        {"user_id": user_id, "title": "Эксперт", 
         "description": "Отправить 50 запросов", "icon": "⭐", "is_unlocked": False},
        {"user_id": user_id, "title": "Мастер", 
         "description": "Отправить 100 запросов", "icon": "🏆", "is_unlocked": False},
        {"user_id": user_id, "title": "Легенда", 
         "description": "Отправить 500 запросов", "icon": "👑", "is_unlocked": False},
    ]
    await db.achievements.insert_many(initial_achievements)
    
    # Создаем токен
    token = create_access_token({"sub": user_id})
    
    return TokenResponse(
        token=token,
        user=UserResponse(
            id=user_id,
            email=user_dict["email"],
            name=user_dict.get("name"),
            phone=user_dict.get("phone"),
            avatar_url=user_dict.get("avatar_url"),
            created_at=user_dict["created_at"]
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    db = get_database()
    
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        print(f"❌ Login failed for email: {login_data.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Преобразуем ObjectId в строку
    user_id = str(user["_id"])
    print(f"✅ User logged in: {user['email']}, ID: {user_id}")
    
    token = create_access_token({"sub": user_id})
    
    return TokenResponse(
        token=token,
        user=UserResponse(
            id=user_id,
            email=user["email"],
            name=user.get("name"),
            phone=user.get("phone"),
            avatar_url=user.get("avatar_url"),
            created_at=user["created_at"]
        )
    )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    db = get_database()
    
    user = await db.users.find_one({"email": request.email})
    if not user:
        return {"message": "If email exists, reset code will be sent"}
    
    # Генерируем 6-значный код
    code = ''.join(random.choices(string.digits, k=6))
    reset_codes[request.email] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=15)
    }
    
    print(f"📧 Reset code for {request.email}: {code}")
    
    return {"message": "Reset code sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    reset_data = reset_codes.get(request.email)
    
    if not reset_data or reset_data["code"] != request.code:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    if reset_data["expires"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired")
    
    db = get_database()
    hashed_password = get_password_hash(request.new_password)
    
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
    )
    
    # Удаляем использованный код
    del reset_codes[request.email]
    
    return {"message": "Password updated successfully"}

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

@router.get("/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    return {
        "user": UserResponse(
            id=str(current_user["_id"]),
            email=current_user["email"],
            name=current_user.get("name"),
            phone=current_user.get("phone"),
            avatar_url=current_user.get("avatar_url"),
            created_at=current_user["created_at"]
        )
    }