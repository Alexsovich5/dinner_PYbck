from pydantic import BaseModel, EmailStr
from typing import Optional

from app.schemas.profile import Profile


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class UserWithProfile(UserBase):
    id: int
    is_active: bool
    profile: Optional[Profile] = None

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str