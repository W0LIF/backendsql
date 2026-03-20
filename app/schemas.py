from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

class User(UserBase):
    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# Auth schemas
class Token(BaseModel):
    token: str
    user: User

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

# Achievement schemas
class AchievementBase(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    condition_type: str
    condition_value: int
    points: int

class Achievement(AchievementBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class UserAchievement(BaseModel):
    id: int
    user_id: int
    achievement_id: int
    earned_at: datetime
    achievement: Achievement
    
    model_config = ConfigDict(from_attributes=True)

# Stats schemas
class UserStats(BaseModel):
    query_count: int
    streak_days: int
    total_days: int
    achievements_count: int
    
    model_config = ConfigDict(from_attributes=True)

# Query schemas
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    query_count: int
    new_achievements: List[Achievement] = []

class QueryHistory(BaseModel):
    query: str
    response: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Password change
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Achievement response
class AchievementResponse(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    unlocked_at: Optional[datetime] = None
    is_unlocked: bool = False

# Stats response
class StatsResponse(BaseModel):
    query_count: int
    streak_days: int
    total_days: int
    achievements_count: int

# Bot query
class BotQueryRequest(BaseModel):
    query: str
    city: str = "samara"

class BotQueryResponse(BaseModel):
    response: str
    query_count: int
    new_achievements: List[Dict[str, Any]] = []

# History response
class HistoryResponse(BaseModel):
    query: str
    response: str
    created_at: str