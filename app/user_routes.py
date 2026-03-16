from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import Optional
import os
import shutil
from datetime import datetime

from .schemas import UserUpdate as UpdateProfileRequest, ChangePasswordRequest
from .models import UserResponse
from .auth_routes import get_current_user, get_password_hash, verify_password
from .database import get_database

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/profile", response_model=dict)
async def get_profile(current_user: dict = Depends(get_current_user)):
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

@router.put("/profile", response_model=dict)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
    if not update_data:
        return {"user": current_user}
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    
    return {
        "user": UserResponse(
            id=str(updated_user["_id"]),
            email=updated_user["email"],
            name=updated_user.get("name"),
            phone=updated_user.get("phone"),
            avatar_url=updated_user.get("avatar_url"),
            created_at=updated_user["created_at"]
        )
    }

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Создаем директорию для аватаров если её нет
    os.makedirs("uploads/avatars", exist_ok=True)
    
    # Генерируем имя файла
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{current_user['_id']}{file_extension}"
    file_path = f"uploads/avatars/{file_name}"
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # URL для доступа к аватару
    avatar_url = f"/static/avatars/{file_name}"
    
    # Обновляем в базе
    db = get_database()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"avatar_url": avatar_url, "updated_at": datetime.utcnow()}}
    )
    
    return {"avatar_url": avatar_url}

@router.delete("/avatar")
async def delete_avatar(current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Удаляем файл если есть
    if current_user.get("avatar_url"):
        file_path = current_user["avatar_url"].replace("/static/", "uploads/")
        if os.path.exists(file_path):
            os.remove(file_path)
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"avatar_url": None, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Avatar deleted"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    if not verify_password(password_data.current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    db = get_database()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "hashed_password": get_password_hash(password_data.new_password),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Password changed successfully"}