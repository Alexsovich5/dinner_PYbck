from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    cuisine_preferences: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class Profile(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True