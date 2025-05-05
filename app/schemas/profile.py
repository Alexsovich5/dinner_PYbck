from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List, Union
from enum import Enum

# Constants for URL prefixes
HTTP_PREFIX = "http://"
HTTPS_PREFIX = "https://"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    
    # Photo fields - make URLs more flexible by accepting strings
    avatar_url: Optional[Union[HttpUrl, str]] = None
    profile_photos: Optional[List[Union[HttpUrl, str]]] = None
    
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

    # Validators to handle string URLs
    @validator('avatar_url', pre=True)
    def validate_avatar_url(cls, v):
        if isinstance(v, str) and v and \
           not v.startswith((HTTP_PREFIX, HTTPS_PREFIX)):
            return f"{HTTPS_PREFIX}{v}"
        return v
    
    @validator('profile_photos', each_item=True, pre=True)
    def validate_profile_photos(cls, v):
        if isinstance(v, str) and v and \
           not v.startswith((HTTP_PREFIX, HTTPS_PREFIX)):
            return f"{HTTPS_PREFIX}{v}"
        return v


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass
    # If 'url' or 'verification_document' fields are needed,
    # they should be added to ProfileBase or ProfileUpdate.
    # Removed validators for non-existent fields 'url' and
    # 'verification_document'.


class Profile(ProfileBase):
    id: int