from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    
    # Photo fields
    avatar_url: Optional[HttpUrl] = None
    profile_photos: Optional[List[HttpUrl]] = None
    
    # Basic preferences
    cuisine_preferences: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    
    # Enhanced preferences
    cooking_level: Optional[str] = None
    preferred_dining_time: Optional[str] = None
    preferred_meal_types: Optional[str] = None
    preferred_group_size: Optional[int] = None
    food_allergies: Optional[str] = None
    special_diets: Optional[str] = None
    favorite_cuisines: Optional[str] = None
    price_range: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfilePhoto(BaseModel):
    url: HttpUrl
    is_primary: bool = False


class VerificationRequest(BaseModel):
    verification_method: str
    verification_document: Optional[HttpUrl] = None


class Profile(ProfileBase):
    id: int
    user_id: int
    is_verified: bool
    verification_status: VerificationStatus
    verification_date: Optional[datetime] = None
    verification_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True